# Generated by Django 3.0.4 on 2020-04-16 09:57

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_auto_20200411_1254'),
    ]

    operations = [
        migrations.CreateModel(
            name='Eq_stoptime',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('eq_id', models.IntegerField(blank=True, null=True)),
                ('stop_time', models.DateTimeField(blank=True, null=True)),
                ('start_time', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'eq_stoptime',
                'managed': True,
            },
        ),
        migrations.AlterField(
            model_name='comment',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 16, 12, 57, 52, 989638)),
        ),
    ]
