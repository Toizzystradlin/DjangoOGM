# Generated by Django 3.0.4 on 2020-09-27 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0066_area_masters'),
    ]

    operations = [
        migrations.AddField(
            model_name='queries',
            name='confirmed',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
