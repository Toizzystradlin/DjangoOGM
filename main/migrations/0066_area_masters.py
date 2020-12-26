# Generated by Django 3.0.4 on 2020-09-27 09:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0065_maintenance_reason'),
    ]

    operations = [
        migrations.CreateModel(
            name='Area_masters',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area', models.CharField(blank=True, max_length=45, null=True)),
                ('tg_id', models.CharField(blank=True, max_length=25, null=True)),
                ('fio', models.CharField(blank=True, max_length=45, null=True)),
            ],
            options={
                'db_table': 'area_masters',
                'managed': True,
            },
        ),
    ]
