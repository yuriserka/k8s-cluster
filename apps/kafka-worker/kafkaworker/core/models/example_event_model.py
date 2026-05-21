from django.db import models
from concurrency.fields import AutoIncVersionField
from kafkaworker.core.models.mixins.pessimistic_locking_save_mixin import PessimisticLockingSaveMixin


class ExampleEventModel(PessimisticLockingSaveMixin, models.Model):
    class Meta:
        db_table = 'example_events'

    LOG_IDENTIFIER_FIELD = 'event_id'
    JSON_MERGE_FIELDS = frozenset({'payload'})

    version = AutoIncVersionField(null=True, default=1)
    id = models.AutoField(auto_created=True, primary_key=True, serialize=False)
    event_id = models.CharField(max_length=36)
    event_type = models.CharField(max_length=255)
    payload = models.JSONField(null=False, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    async def asave(
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: list[str] | None = None,
    ):
        if self._state.adding:
            return await super().asave(
                force_insert=force_insert,
                force_update=force_update,
                using=using,
                update_fields=update_fields,
            )

        return await self.save_under_lock(
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
