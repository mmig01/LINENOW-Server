# Generated by Django 5.1.1 on 2025-05-21 13:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booth', '0004_booth_manager_contact'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booth',
            name='manager_contact',
        ),
    ]
