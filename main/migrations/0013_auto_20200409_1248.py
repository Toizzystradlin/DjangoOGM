# Generated by Django 3.0.4 on 2020-04-09 09:48

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_auto_20200408_2226'),
    ]

    operations = [
        migrations.AddField(
            model_name='employees',
            name='tg_id',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 9, 12, 48, 28, 847621)),
        ),
    ]