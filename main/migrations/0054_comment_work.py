# Generated by Django 3.0.4 on 2020-08-12 17:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0053_worktime_work_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='work',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
