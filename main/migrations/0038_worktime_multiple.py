# Generated by Django 3.0.4 on 2020-04-29 20:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0037_queries_multiple'),
    ]

    operations = [
        migrations.AddField(
            model_name='worktime',
            name='multiple',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
