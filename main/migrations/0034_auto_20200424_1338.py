# Generated by Django 3.0.4 on 2020-04-24 10:38

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0033_auto_20200424_1245'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queries',
            name='test_emp',
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
    ]
