from .models import Queries, Equipment, Employees, Comment, Maintenance, Worktime, Eq_stoptime, Unstated_works
from datetime import datetime, timedelta, timezone
import pytz
#import datetime
import json
from django.db import connection
from . import send_message
import xlwt
from django.http import HttpResponse
from django.db.models import Q
import time

def employee_timeline(employee_id):
    fio = Employees.objects.get(employee_id=employee_id).fio

    queries = Worktime.objects.filter(employee_id=employee_id)
    q = []
    for i in queries:
        if i.query_id not in q:
            q.append(i.query_id)
    data = {}
    for num, i in enumerate(q, start=0):
        worktimes = Worktime.objects.filter(query_id=i)
        times_full = []
        for j in worktimes:
            times = []
            try:
                times.append(num)
                times.append(j.start_time.year)
                times.append(j.start_time.month)
                times.append(j.start_time.day)
                times.append(j.start_time.hour)
                times.append(j.start_time.minute)
                times.append(j.stop_time.year)
                times.append(j.stop_time.month)
                times.append(j.stop_time.day)
                times.append(j.stop_time.hour)
                times.append(j.stop_time.minute)
                times_full.append(times)
            except: None
        try:
            query = Queries.objects.get(query_id=i)
            eq = Equipment.objects.get(eq_id=query.eq_id)
            data['Заявка №' + str(i) + ' ' + str(eq.eq_name)] = times_full
        except:
            data['Заявка №' + str(i)] = times_full
    return data, fio

def employee_timeline_period(employee_id, date1, date2):
    fio = Employees.objects.get(employee_id=employee_id).fio
    class Worktime_for_query:
        def __init__(self):
            self.query_id = None
            self.eq_id = None
            self.eq_name = None
            self.start_time = None
            self.stop_time = None

    queries = Worktime.objects.filter(employee_id=employee_id)
    q = []
    for i in queries:
        if i.query_id not in q:
            q.append(i.query_id)
    data = {}
    for num, i in enumerate(q, start=0):
        worktimes = Worktime.objects.filter(query_id=i)
        times_full = []
        for j in worktimes:
            times = []
            try:
                worktime_for_query = Worktime_for_query()
                if (date2.date() < j.stop_time.date()) and (date1.date() > j.start_time.date()) and (j.start_time.date() < date2.date()): #начало внутри, а конец после периода
                    worktime_for_query.start_time = j.start_time
                    worktime_for_query.stop_time = date2
                elif (date2.date() <= j.stop_time.date()) and (date1.date() >= j.start_time.date()): # начало до, а конец после
                    worktime_for_query.start_time = date1
                    worktime_for_query.stop_time = date2
                elif (j.start_time.date() <= date1.date() and j.stop_time.date() >= date1.date() and j.stop_time.date() <= date2.date()): # начало до периода, а конец внутри
                    worktime_for_query.start_time = date1
                    worktime_for_query.stop_time = j.stop_time
                elif ((date1.date() <= j.start_time.date()) and (date2.date() >= j.stop_time.date())): # строго внутри интервала
                    worktime_for_query.start_time = j.start_time
                    worktime_for_query.stop_time = j.stop_time
                #else:
                #    worktime_for_query.start_time = datetime.now()
                #    worktime_for_query.stop_time = datetime.now() + timedelta(hours=1)
                worktime_for_query.query_id = j.query_id
                #eq_id = Queries.objects.get(query_id=j.query_id).eq_id
                #eq_name = Equipment.objects.get(eq_id=eq_id).eq_name
                #worktime_for_query.eq_id = eq_id
                #worktime_for_query.eq_name = eq_name
                times.append(num)
                #try:
                times.append(worktime_for_query.start_time.year)
                times.append(worktime_for_query.start_time.month)
                times.append(worktime_for_query.start_time.day)
                times.append(worktime_for_query.start_time.hour)
                times.append(worktime_for_query.start_time.minute)
                times.append(worktime_for_query.stop_time.year)
                times.append(worktime_for_query.stop_time.month)
                times.append(worktime_for_query.stop_time.day)
                times.append(worktime_for_query.stop_time.hour)
                times.append(worktime_for_query.stop_time.minute)
                times_full.append(times)
            except: pass

            #except:
            #    data[str(i)] = times_full
        data['Заявка №' + str(i)] = times_full
    return data, fio
