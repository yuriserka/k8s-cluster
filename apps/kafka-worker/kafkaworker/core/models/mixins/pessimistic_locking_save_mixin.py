import logging

from django.db.models.base import sync_to_async
from jsondiff import diff as compute_json_diff, patch as apply_json_patch
from django.db import models, transaction

logger = logging.getLogger(__name__)


def _top_level_merge(snapshot_value, current_value, database_value):
    """Fallback merge when jsondiff.patch fails due to a missing key.

    Applies additions and changes from current onto database, and removes
    keys that were deleted relative to the snapshot.
    """
    merged = dict(database_value)
    snapshot = snapshot_value or {}
    current = current_value or {}
    for key, value in current.items():
        if key not in snapshot or snapshot.get(key) != value:
            merged[key] = value
    for key in snapshot:
        if key not in current:
            merged.pop(key, None)
    return merged


def merge_json_changes(snapshot_value, current_value, database_value):
    """Apply nested key changes (snapshot -> current) onto database_value.

    Computes a recursive diff between the snapshot (state at load time) and
    current (state now), then patches the database's fresh value so only
    actual changes are written.  Falls back to a safe top-level merge when
    a concurrent process already deleted a key we also intended to remove.
    """
    if snapshot_value is None or not isinstance(database_value, dict):
        return current_value

    changes = compute_json_diff(snapshot_value or {}, current_value or {})
    try:
        return apply_json_patch(database_value, changes)
    except KeyError:
        return _top_level_merge(snapshot_value, current_value, database_value)


class PessimisticLockingSaveMixin(models.Model):
    """Abstract mixin that provides concurrency-safe saves via SELECT FOR UPDATE.

    Tracks which fields have been modified since construction (dirty tracking)
    and, on save, acquires a row-level lock, copies only dirty fields onto the
    locked row (merging JSON fields instead of overwriting), and persists via
    the locked row's own Model.save().

    Subclass hooks
    --------------
    JSON_MERGE_FIELDS : frozenset
        Field names whose values are dicts that should be merged (not replaced)
        with the database row when saving under lock.
    LOG_IDENTIFIER_FIELD : str or None
        Model field name whose value is used to identify the instance in log
        messages. Falls back to pk when None.
    build_lock_queryset(using) :
        Override to add partition-pruning or extra filters to the
        SELECT FOR UPDATE queryset.
    """

    JSON_MERGE_FIELDS = frozenset()
    LOG_IDENTIFIER_FIELD = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dirty_fields = set()
        self._take_json_field_snapshots()

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if not name.startswith('_'):
            dirty = self.__dict__.get('_dirty_fields')
            if dirty is not None and name in self._get_tracked_field_names():
                dirty.add(name)

    @classmethod
    def _get_tracked_field_names(cls):
        cached = cls.__dict__.get('_tracked_fields_cache')
        if cached is not None:
            return cached
        tracked = frozenset(
            field.name for field in cls._meta.local_concrete_fields
            if not field.primary_key and field.name != 'version'
        )
        cls._tracked_fields_cache = tracked
        return tracked

    def mark_field_as_dirty(self, field_name):
        dirty = self.__dict__.get('_dirty_fields')
        if dirty is not None:
            dirty.add(field_name)

    def get_dirty_field_names(self, explicit_update_fields=None):
        """Return field names that need saving, excluding version.

        Version is excluded because it is managed by django-concurrency's
        PartitionAwareAutoIncVersionField and must not be copied from the
        in-memory instance (which may hold a stale value).
        """
        if explicit_update_fields is not None:
            return [name for name in explicit_update_fields if name != 'version']

        dirty = self.__dict__.get('_dirty_fields')
        if dirty is not None:
            return [name for name in dirty if name != 'version']

        return [
            field.name
            for field in type(self)._meta.local_concrete_fields
            if not field.primary_key and field.name != 'version'
        ]

    def refresh_from_db(self, using=None, fields=None, **kwargs):
        super().refresh_from_db(using=using, fields=fields, **kwargs)
        if fields is None:
            self._dirty_fields = set()
            self._take_json_field_snapshots()
        else:
            self._dirty_fields -= set(fields)
            if any(name in fields for name in self.JSON_MERGE_FIELDS):
                self._take_json_field_snapshots()

    def _take_json_field_snapshots(self):
        self._json_field_snapshots = {}
        for field_name in self.JSON_MERGE_FIELDS:
            value = self.__dict__.get(field_name)
            self._json_field_snapshots[field_name] = (
                dict(value) if isinstance(value, dict) else value
            )

    def build_lock_queryset(self, using):
        model_class = type(self)
        queryset = model_class.objects.select_for_update()
        if using is not None:
            queryset = queryset.using(using)
        return queryset

    def _get_log_identifier(self):
        field = self.LOG_IDENTIFIER_FIELD
        if field is not None:
            return getattr(self, field, self.pk)
        return self.pk

    @sync_to_async
    def save_under_lock(
        self,
        *,
        force_update: bool = False,
        using: str | None = None,
        update_fields: list[str] | None = None,
    ):
        """SELECT FOR UPDATE the row, copy dirty fields, and persist.

        For fields listed in JSON_MERGE_FIELDS the value is *merged* with the
        database row (preserving concurrent changes to other keys) rather than
        blindly overwritten.  All other dirty fields are copied directly.
        """
        dirty_field_names = self.get_dirty_field_names(update_fields)
        if not dirty_field_names:
            return self

        update_field_names_with_version = list(
            dict.fromkeys(dirty_field_names + ['version', 'updated_at'])
        )

        model_name = type(self).__name__
        log_id = self._get_log_identifier()

        with transaction.atomic(using=using):
            logger.info(
                "[%s] Saving %s under lock | memory_version=%s | dirty_fields=%s",
                model_name, log_id, self.version, dirty_field_names,
            )

            locked_row = self.build_lock_queryset(using).get(pk=self.pk)
            logger.info(
                "[%s] Locked %s | database_version=%s",
                model_name, log_id, locked_row.version,
            )

            for field_name in dirty_field_names:
                database_value = getattr(locked_row, field_name)
                memory_value = getattr(self, field_name)

                if field_name in self.JSON_MERGE_FIELDS:
                    snapshot_value = self._json_field_snapshots.get(field_name)
                    merged_value = merge_json_changes(
                        snapshot_value, memory_value, database_value,
                    )
                    setattr(locked_row, field_name, merged_value)
                    logger.info(
                        "[%s] %s field=%s | diff_after_merge=%s",
                        model_name, log_id, field_name,
                        compute_json_diff(snapshot_value, merged_value),
                    )
                else:
                    setattr(locked_row, field_name, memory_value)

            super(type(self), locked_row).save(
                force_insert=False,
                force_update=force_update,
                using=using,
                update_fields=update_field_names_with_version,
            )

            logger.info(
                "[%s] Saved %s | new_version=%s",
                model_name, log_id, locked_row.version,
            )

        self._sync_from_locked_row(locked_row)
        return self

    def _sync_from_locked_row(self, locked_row):
        """Copy all non-PK field values from the locked row back to self."""
        for field in type(self)._meta.local_concrete_fields:
            if not field.primary_key:
                setattr(self, field.name, getattr(locked_row, field.name))
        self._dirty_fields = set()
        self._take_json_field_snapshots()
