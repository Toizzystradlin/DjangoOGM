# Generated by Django 3.0.4 on 2020-04-09 17:52

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_auto_20200409_1257'),
    ]

    operations = [
        migrations.AddField(
            model_name='queries',
            name='big_delta',
            field=models.DurationField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='queries',
            name='end_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='queries',
            name='restart_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='queries',
            name='small_delta',
            field=models.DurationField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 9, 20, 52, 52, 296536)),
        ),
        migrations.AlterField(
            model_name='employees',
            name='master',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]