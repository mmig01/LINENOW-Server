# Generated by Django 5.1.1 on 2025-05-26 00:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_smsauthenticate_sms_count'),
    ]

    operations = [
        migrations.RenameField(
            model_name='smsauthenticate',
            old_name='sms_count',
            new_name='bad_sms_count',
        ),
    ]
