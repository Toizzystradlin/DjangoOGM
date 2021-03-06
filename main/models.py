# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import User
import jsonfield

import datetime

class Queries(models.Model):
    query_id = models.AutoField(primary_key=True)
    query_name = models.CharField(max_length=45, blank=True, null=True)
    eq_id = models.IntegerField(blank=True, null=True)
    post_time = models.DateTimeField(blank=True, null=True)
    reason = models.CharField(max_length=45, blank=True, null=True)
    msg = models.TextField(blank=True, null=True)
    query_status = models.CharField(max_length=45, blank=True, null=True)
    employee_id = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    stop_time = models.DateTimeField(blank=True, null=True)
    comment = models.CharField(max_length=3000, blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    json_emp = models.CharField(max_length=45, blank=True, null=True)
    multiple = models.IntegerField(blank=True, null=True)
    photo_name = models.CharField(max_length=100, blank=True, null=True)
    confirmed = models.IntegerField(blank=True, null=True)
    appoint_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Queries'



class Equipment(models.Model):
    eq_id = models.AutoField(primary_key=True)
    invnum = models.CharField(max_length=255, blank=True, null=True)
    eq_name = models.CharField(max_length=255, blank=True, null=True)
    eq_type = models.CharField(max_length=255, blank=True, null=True)
    eq_comment = models.CharField(max_length=3000, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    area_choices = [
        ('Механической обработки', 'Механической обработки'),
        ('Слесарный', 'Слесарный'),
        ('Сварочный', 'Сварочный'),
        ('Сборки', 'Сборки'),
        ('Радиомонтажа', 'Радиомонтажа'),
    ]

    area = models.CharField(max_length=45, blank=True, null=True, choices=area_choices)

    eq_status_choices = [
        ('working', 'Работает'),
        ('stopped', 'Остановилось'),
    ]

    eq_status = models.CharField(max_length=45, choices=eq_status_choices, default='Работает', blank=True, null=True)
    shift = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Equipment'


class Employees(models.Model):
    employee_id = models.AutoField(primary_key=True)
    fio = models.CharField(max_length=45, blank=True, null=True)
    rank = models.CharField(max_length=45, blank=True, null=True)
    tg_id = models.CharField(max_length=25, blank=True, null=True)
    master = models.BooleanField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'Employees'


class Comment(models.Model):
    author = models.CharField(max_length=200)
    text = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    query = models.IntegerField(blank=True, null=True)
    work = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Comments'

class Type(models.Model):
    type = models.CharField(max_length=200)

    class Meta:
        managed = True
        db_table = 'types'

class Maintenance(models.Model):
    eq_id = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    employee_id = models.CharField(max_length=50)
    comment = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    status2 = models.CharField(max_length=50, null=True, blank=True)
    month_start = models.DateTimeField(blank=True, null=True)
    shift_start = models.DateTimeField(blank=True, null=True)
    shift_end = models.DateTimeField(blank=True, null=True)
    expected_time = models.IntegerField(blank=True, null=True)
    plan_date = models.DateTimeField(blank=True, null=True)
    plan2_date = models.DateTimeField(blank=True, null=True)
    reason = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=45, null=True, blank=True)
    class Meta:
        managed = True
        db_table = 'maintenance'


class Worktime(models.Model):
    query_id = models.IntegerField(blank=True, null=True)
    employee_id = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    stop_time = models.DateTimeField(blank=True, null=True)
    multiple = models.IntegerField(blank=True, null=True)
    work_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'worktime'

class Eq_stoptime(models.Model):
    eq_id = models.IntegerField(blank=True, null=True)
    stop_time = models.DateTimeField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    month_start = models.DateTimeField(blank=True, null=True)
    shift_start = models.DateTimeField(blank=True, null=True)
    shift_end = models.DateTimeField(blank=True, null=True)
    now = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'eq_stoptime'

class Reasons(models.Model):
    reason = models.CharField(max_length=50, null=True, blank=True)
    class Meta:
        managed = True
        db_table = 'reasons'

class Supplies(models.Model):
    query_id = models.IntegerField(blank=True, null=True)
    eq_id = models.IntegerField(blank=True, null=True)
    supply = models.TextField(blank=True, null=True)
    emp_id = models.IntegerField(blank=True, null=True)
    work_id = models.IntegerField(blank=True, null=True)
    to_id = models.IntegerField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'supplies'

class Dates(models.Model):
    kpi_a_start = models.DateTimeField(blank=True, null=True)
    kpi_a_end = models.DateTimeField(blank=True, null=True)
    chart = models.CharField(max_length=50, null=True, blank=True)
    class Meta:
        managed = True
        db_table = 'dates'

class Unstated_works(models.Model):
    work_id = models.AutoField(primary_key=True)
    what = models.CharField(max_length=400, blank=True, null=True)
    post_time = models.DateTimeField(blank=True, null=True)
    query_status = models.CharField(max_length=45, blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    stop_time = models.DateTimeField(blank=True, null=True)
    comment = models.CharField(max_length=3000, blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    json_emp = models.CharField(max_length=45, blank=True, null=True)
    multiple = models.IntegerField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'unstated_works'

class Daily_tasks(models.Model):
    task_id = models.AutoField(primary_key=True)
    date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    task = models.CharField(max_length=3000, blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'daily_tasks'

class Area_masters(models.Model):
    area = models.CharField(max_length=45, blank=True, null=True)
    tg_id = models.CharField(max_length=25, blank=True, null=True)
    fio = models.CharField(max_length=45, blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'area_masters'