# Generated by Django 5.1.7 on 2025-03-12 03:34

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS example_events (
                id SERIAL NOT NULL,
                event_id VARCHAR(36) NOT NULL,
                event_type VARCHAR(255) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                username VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                CONSTRAINT example_events_pk PRIMARY KEY (id)
            );

            CREATE INDEX IF NOT EXISTS example_events_user_id_idx ON example_events (user_id);
            """,
            state_operations=[
                migrations.CreateModel(
                    name='ExampleEventModel',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                        ('event_id', models.CharField(max_length=36)),
                        ('event_type', models.CharField(max_length=255)),
                        ('user_id', models.CharField(db_index=True, max_length=36)),
                        ('username', models.CharField(max_length=255)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        'db_table': 'example_events',
                    },
                ),
            ]
        ),
    ]
