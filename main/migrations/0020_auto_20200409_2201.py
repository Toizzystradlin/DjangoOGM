# Generated by Django 3.0.4 on 2020-04-09 19:01

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_auto_20200409_2151'),
    ]

    operations = [
        migrations.CreateModel(
            name='Worktime',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query_id', models.IntegerField(blank=True, null=True)),
                ('employee_id', models.IntegerField(blank=True, null=True)),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('stop_time', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'worktime',
                'managed': True,
            },
        ),
        migrations.AlterField(
            model_name='comment',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 9, 22, 1, 41, 825984)),
        ),
    ]