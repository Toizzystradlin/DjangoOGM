# Generated by Django 3.0.4 on 2020-05-22 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0043_delete_reasons'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reasons',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'db_table': 'reasons',
                'managed': True,
            },
        ),
        migrations.AlterField(
            model_name='maintenance',
            name='status',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]