# Generated by Django 5.1.1 on 2025-04-29 23:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_user_no_show_num_customeruser_no_show_num'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='login_id',
            new_name='user_phone',
        ),
    ]
