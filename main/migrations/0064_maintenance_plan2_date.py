# Generated by Django 3.0.4 on 2020-09-20 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0063_auto_20200909_1913'),
    ]

    operations = [
        migrations.AddField(
            model_name='maintenance',
            name='plan2_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]