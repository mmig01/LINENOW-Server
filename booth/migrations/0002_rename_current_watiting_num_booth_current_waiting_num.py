# Generated by Django 5.1.1 on 2025-05-12 15:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booth', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='booth',
            old_name='current_watiting_num',
            new_name='current_waiting_num',
        ),
    ]
