# Generated by Django 5.1.7 on 2025-05-16 17:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('filesharing', '0002_alter_collection_project'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subcollections', to='filesharing.collection'),
        ),
    ]
