# Generated by Django 3.0.4 on 2020-08-11 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0052_unstated_works'),
    ]

    operations = [
        migrations.AddField(
            model_name='worktime',
            name='work_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
