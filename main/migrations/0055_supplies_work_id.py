# Generated by Django 3.0.4 on 2020-08-12 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0054_comment_work'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplies',
            name='work_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]