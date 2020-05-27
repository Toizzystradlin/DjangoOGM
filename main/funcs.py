from .models import Queries, Equipment, Employees, Comment, Maintenance, Worktime, Eq_stoptime
from datetime import datetime, timedelta, timezone
import json
from django.db import connection
from . import send_message
import xlwt
from django.http import HttpResponse


def top10(equipment):
    pairs = []
    for i1 in equipment:
        shifts = i1.shift
        eq_id = i1.eq_id
        n = Eq_stoptime.objects.filter(eq_id=eq_id)  # блок высчитывает время простоя
        duration = timedelta(microseconds=0)  # он добавляет в бд текущее время, а потом удаляет его
        for i in n:
            if i.start_time == None:
                i.start_time = datetime.now()
                w = 1
                i.save()
        n = Eq_stoptime.objects.filter(eq_id=eq_id)  # по новой получаем список, так как он изменился
        for i in n:
            start_year = i.stop_time.year
            start_month = i.stop_time.month
            start_day = i.stop_time.day
            end_year = i.start_time.year
            end_month = i.start_time.month
            end_day = i.start_time.day
            if shifts == 1:
                i.shift_end = datetime(start_year, start_month, start_day, 15)
            else:
                i.shift_end = datetime(start_year, start_month, start_day, 23)
            i.shift_start = datetime(end_year, end_month, end_day, 7)
            i.save()

        n = Eq_stoptime.objects.filter(eq_id=eq_id)  # по новой получаем список, так как он изменился
        for i in n:
            i_date = i.stop_time
            if datetime.isoweekday(i.stop_time) < 6:
                j = i.shift_end - i.stop_time
            else:
                j = timedelta(microseconds=0)
            duration = duration + j
            i_date = i_date + timedelta(hours=24)
            while i_date < i.shift_start:  # Тут мы прибавляем по 8 часов за каждую смену каждого рабочего дня
                if datetime.isoweekday(i_date) < 6:
                    duration = duration + timedelta(hours=8) * shifts
                i_date = i_date + timedelta(hours=24)
            if datetime.isoweekday(i.start_time) < 6:
                j = i.start_time - i.shift_start
            else:
                j = timedelta(microseconds=0)
            duration = duration + j

        n = list(Eq_stoptime.objects.filter(eq_id=eq_id))
        try:
            if w == 1:
                i = n[-1]
                i.start_time = None
                i.save()
                w = 0
        except:
            pass
        pair = (i1.eq_name, duration.total_seconds() / 3600, shifts)
        pairs.append(pair)
    pairs = sorted(pairs, key=lambda x: x[1])  # сортировка по увеличению дней в простое
    pairs.reverse()
    pairs = pairs[:10]  # обрезка до 10 штук
    names = []
    means = []
    sh = []
    for j in pairs:
        names.append(j[0])
        means.append(j[1])
        sh.append(j[2])
    return names, means, sh


def top10_month(equipment):
    today = datetime.now()  # топ 10 по простою за месяц
    this_month = today.month
    this_year = today.year
    stops = Eq_stoptime.objects.all()
    for q1 in stops:
        q1.month_start = datetime(this_year, this_month, 1)
        q1.save()
    pairs_m = []
    for j1 in equipment:
        shifts = j1.shift
        eq_id = j1.eq_id
        n = Eq_stoptime.objects.filter(eq_id=eq_id)
        duration2 = timedelta(microseconds=0)
        for i in n:
            if i.start_time == None:
                i.start_time = datetime.now()
                i.save()
                w = 1
        n = Eq_stoptime.objects.filter(eq_id=eq_id)
        for i in n:
            if i.start_time.month == this_month:
                if i.stop_time.month == this_month:
                    i_date = i.stop_time
                    if datetime.isoweekday(i.stop_time) < 6:
                        j = i.shift_end - i.stop_time
                    else:
                        j = timedelta(microseconds=0)
                    duration2 = duration2 + j
                    i_date = i_date + timedelta(hours=24)
                    while i_date < i.shift_start:
                        if datetime.isoweekday(i_date) < 6:
                            duration2 = duration2 + timedelta(hours=8) * shifts
                        i_date = i_date + timedelta(hours=24)
                    if datetime.isoweekday(i.start_time) < 6:
                        j = i.start_time - i.shift_start
                    else:
                        j = timedelta(microseconds=0)
                    duration2 = duration2 + j

                else:
                    i_date = i.month_start
                    if datetime.isoweekday(i_date) < 6:
                        j = i.shift_end - i.stop_time
                    else:
                        j = timedelta(microseconds=0)
                    duration2 = duration2 + j
                    i_date = i_date + timedelta(hours=24)
                    while i_date < i.shift_start:
                        if datetime.isoweekday(i_date) < 6:
                            duration2 = duration2 + timedelta(hours=8) * shifts
                        i_date = i_date + timedelta(hours=24)
                    if datetime.isoweekday(i.start_time) < 6:
                        j = i.start_time - i.shift_start
                    else:
                        j = timedelta(microseconds=0)
                    duration2 = duration2 + j

        n = list(Eq_stoptime.objects.filter(eq_id=eq_id))
        try:
            if w == 1:
                i = n[-1]
                i.start_time = None
                i.save()
                w = 0
        except:
            pass
        pair2 = (j1.eq_name, duration2.total_seconds() / 3600, shifts)
        pairs_m.append(pair2)
    pairs_m = sorted(pairs_m, key=lambda x: x[1])  # сортировка по увеличению дней в простое
    pairs_m.reverse()
    pairs_m = pairs_m[:10]  # обрезка до 10 штук
    names_m = []
    means_m = []
    sh_m = []
    for j in pairs_m:
        names_m.append(j[0])
        means_m.append(j[1])
        sh_m.append(j[2])
    return names_m, means_m, sh_m


def appoint_doers(doers, query_id):
    doers_dict = {'doers': doers}
    doers_json = json.dumps(doers_dict)
    query = Queries.objects.get(query_id=query_id)
    query.json_emp = doers_json
    query.save()
    for doer in doers:
        doer_query = Employees.objects.get(employee_id=doer)
        doer_id = doer_query.tg_id
        send_message.send_message_4(doer_id, query_id)

def appoint_doers_to(doers, to_id):
    doers_dict = {'doers': doers}
    doers_json = json.dumps(doers_dict)
    to = Maintenance.objects.get(id=to_id)
    to.employee_id = doers_json
    to.save()


def appoint_doers_2(doers, query_id):
    doers_dict = {'doers': doers}
    doers_json = json.dumps(doers_dict)
    query = Queries.objects.get(query_id=query_id)
    query.json_emp = doers_json
    query.save()

def multiple_doers(doers, query_id):
    q = Queries.objects.get(query_id=query_id)
    if len(doers) > 1:
        q.multiple = 1
        q.save()
    else:
        q.multiple = 0
        q.save()

