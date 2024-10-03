# Generated by Django 5.1.1 on 2024-10-03 13:35

import booth.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Booth',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='부스명')),
                ('description', models.TextField(verbose_name='부스 설명')),
                ('caution', models.TextField(verbose_name='부스 유의사항')),
                ('location', models.CharField(max_length=255, verbose_name='부스 위치')),
                ('is_operated', models.CharField(choices=[('not_started', 'Not Started'), ('operating', 'Operating'), ('finished', 'Finished')], max_length=100, verbose_name='운영 여부')),
                ('open_time', models.DateTimeField(verbose_name='시작 시간')),
                ('close_time', models.DateTimeField(verbose_name='마감 시간')),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='행사명')),
            ],
        ),
        migrations.CreateModel(
            name='BoothImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to=booth.models.image_upload_path)),
                ('booth', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boothimages', to='booth.booth')),
            ],
        ),
        migrations.CreateModel(
            name='BoothMenu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='메뉴 이름')),
                ('price', models.IntegerField(verbose_name='가격')),
                ('booth', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='menus', to='booth.booth')),
            ],
        ),
        migrations.AddField(
            model_name='booth',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booths', to='booth.event'),
        ),
    ]
