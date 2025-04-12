# Generated by Django 5.1.1 on 2025-04-13 00:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('booth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Waiting',
            fields=[
                ('waiting_id', models.AutoField(primary_key=True, serialize=False)),
                ('person_num', models.IntegerField(verbose_name='인원 수')),
                ('waiting_status', models.CharField(choices=[('waiting', 'waiting'), ('canceled', 'canceled'), ('entered', 'entered'), ('entering', 'entering'), ('not_waiting', 'not_waiting'), ('time_over', 'time_over')], default='waiting', max_length=20, verbose_name='대기 상태')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='대기 생성 시간')),
                ('confirmed_at', models.DateTimeField(blank=True, null=True, verbose_name='대기 호출 시간')),
                ('canceled_at', models.DateTimeField(blank=True, null=True, verbose_name='대기 취소 시간')),
                ('arrived_at', models.DurationField(blank=True, null=True, verbose_name='입장 시간')),
                ('booth', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='waitings', to='booth.booth')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='waitings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
