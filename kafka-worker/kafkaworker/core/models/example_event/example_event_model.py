from django.db import models


class ExampleEventModel(models.Model):
    class Meta:
        db_table = 'example_events'

    event_id = models.CharField(max_length=36, primary_key=True)
    event_type = models.CharField(max_length=255)
    user_id = models.CharField(max_length=36, db_index=True)
    username = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
