# Generated by Django 3.0.4 on 2020-07-28 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0048_maintenance_expected_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipment',
            name='category',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
