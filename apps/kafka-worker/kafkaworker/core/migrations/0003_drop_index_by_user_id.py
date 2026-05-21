from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_payload_and_version_columns'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS example_events_user_id_idx;",
        )
    ]
