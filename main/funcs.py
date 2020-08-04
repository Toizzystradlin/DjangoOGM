from .models import Queries, Equipment, Employees, Comment, Maintenance, Worktime, Eq_stoptime
from datetime import datetime, timedelta, timezone
import pytz
#import datetime
import json
from django.db import connection
from . import send_message
import xlwt
from django.http import HttpResponse
from django.db.models import Q

def queries_and_to():
    today = datetime.today()
    day = today.day
    delta = timedelta(days=day)
    month_start = today - delta
    this_month = today.month
    utc = pytz.UTC
    month_start = utc.localize(month_start)
    queries = Queries.objects.all()
    m = Maintenance.objects.filter(status='Завершено')
    queries_count = 0
    tos_count = 0
    duration_to = timedelta(microseconds=0)
    pairs = []
    for i in queries:
        if i.post_time > month_start:
            queries_count = queries_count + 1
    for i in m:
        eq = Equipment.objects.get(eq_id=i.eq_id)
        eq_name = eq.eq_name
        if i.start_time.month == this_month:
            if i.start_time > month_start:
                tos_count += 1
                if i.start_time.date() == i.end_time.date():
                    duration_to = i.end_time - i.start_time
                else:
                    duration_to = i.shift_end - i.start_time
                    stop = False
                    i_date = i.start_time + timedelta(hours=24)
                    while stop == False:
                        if i_date.date() == i.end_time.date():
                            j = i.end_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                j = timedelta(hours=8)
                            else:
                                j = timedelta(seconds=0)
                        duration_to = duration_to + j
                        if i_date.date() == i.end_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
            pair = (eq_name, duration_to.total_seconds() / 3600, i.expected_time)
            pairs.append(pair)

    return queries_count, tos_count, pairs

def plain_period(equipment, s1, s2):
    utc = pytz.UTC
    period_start = datetime(year=s1[0], month=s1[1], day=s1[2])
    period_end = datetime(year=s2[0], month=s2[1], day=s2[2])
    pairs = []
    for i1 in equipment:
        stops = Eq_stoptime.objects.filter(eq_id = i1.eq_id)
        full_duration = timedelta(microseconds=0)
        full_duration_to = timedelta(microseconds=0)
        duration = timedelta(microseconds=0)
        for stop in stops:
            duration = timedelta(microseconds=0)
            if stop.start_time is not None:
                start_time = stop.start_time
            else:
                start_time = utc.localize(datetime.now())
            if (stop.stop_time.date() == start_time.date()) and (period_start.date() <= stop.stop_time.date() <= period_end.date()):
                duration = start_time - stop.stop_time
            elif period_start.date() <= stop.stop_time.date() <= period_end.date():
                duration = stop.shift_end - stop.stop_time
                cancel = False
                i_date = stop.stop_time + timedelta(hours=24)
                while cancel == False:
                    if (i_date.date() == start_time.date()):
                        j = start_time - stop.shift_start
                    else:
                        if datetime.isoweekday(i_date.date()) < 6:
                            j = timedelta(hours=8) * i1.shift
                        else:
                            j = timedelta(seconds=0)
                    duration = duration + j
                    if (i_date.date() == start_time.date()) or (i_date.date() >= period_end.date()):
                        cancel = True
                    i_date = i_date + timedelta(hours=24)
            elif (stop.stop_time.date() < period_start.date()) and (start_time.date() >= period_start.date()):
                cancel = False
                i_date = period_start
                while cancel == False:
                    if (i_date.date() == start_time.date()):
                        j = start_time - stop.shift_start
                    else:
                        if datetime.isoweekday(i_date.date()) < 6:
                            j = timedelta(hours=8) * i1.shift
                        else:
                            j = timedelta(seconds=0)
                    duration = duration + j
                    if (i_date.date() == start_time.date()) or (i_date.date() >= period_end.date()):
                        cancel = True
                    i_date = i_date + timedelta(hours=24)
            full_duration = full_duration + duration
        maints = Maintenance.objects.filter(eq_id = i1.eq_id)
        maints = maints.exclude(status='Новое')
        for maint in maints:
            duration_to = timedelta(microseconds=0)
            if maint.end_time is not None:
                end_time = maint.end_time
            else:
                end_time = utc.localize(datetime.now())
            if (maint.start_time.date() == end_time.date()) and (period_start.date() <= maint.start_time.date() <= period_end.date()):
                duration_to = end_time - maint.start_time
            elif period_start.date() <= maint.start_time.date() <= period_end.date():
                duration_to = maint.shift_end - maint.start_time
                cancel = False
                i_date = maint.start_time + timedelta(hours=24)
                while cancel == False:
                    if (i_date.date() == end_time.date()):
                        j = end_time - maint.shift_start
                    else:
                        if datetime.isoweekday(i_date.date()) < 6:
                            j = timedelta(hours=8) * i1.shift
                        else:
                            j = timedelta(seconds=0)
                    duration_to = duration_to + j
                    if (i_date.date() == end_time.date()) or (i_date.date() >= period_end.date()):
                        cancel = True
                    i_date = i_date + timedelta(hours=24)
            elif (maint.start_time.date() < period_start.date()) and (end_time.date() >= period_start.date()):
                cancel = False
                i_date = period_start
                while cancel == False:
                    if (i_date.date() == end_time.date()):
                        j = end_time - maint.shift_start
                    else:
                        if datetime.isoweekday(i_date.date()) < 6:
                            j = timedelta(hours=8) * i1.shift
                        else:
                            j = timedelta(seconds=0)
                    duration_to = duration_to + j
                    if (i_date.date() == end_time.date()) or (i_date.date() >= period_end.date()):
                        cancel = True
                    i_date = i_date + timedelta(hours=24)
            full_duration_to = full_duration_to + duration_to
        sum = full_duration.total_seconds() + full_duration_to.total_seconds()
        pair = (i1.eq_name, full_duration.total_seconds() / 3600, full_duration_to.total_seconds() / 3600, i1.invnum, sum)
        pairs.append(pair)


    pairs = sorted(pairs, key=lambda x: x[4])  # сортировка по увеличению дней в простое
    pairs.reverse()
    pairs = pairs[:15]  # обрезка до 10 штук
    names = []
    means = []
    means_to = []
    #sh = []
    invnum = []
    for j in pairs:
        names.append(j[0])
        means.append(j[1])
        means_to.append(j[2])
        #sh.append(j[3])
        invnum.append(j[3])
    return names, means, means_to, invnum

def time_kpi(n, s1='asd', s2='asd', s3='week'):
    start = datetime(year=2020, month=6, day=8)
    end = datetime.now().date()
    step = timedelta(weeks=1)
    try:
        start = datetime(year=s1[0], month=s1[1], day=s1[2])
        end = datetime(year=s2[0], month=s2[1], day=s2[2]).date()
        if s3 == 'day': step = timedelta(days=1)
        if s3 == 'week': step = timedelta(weeks=1)
        if s3 == 'month': step = timedelta(weeks=4)
    except: pass
    #start = datetime(year=2020, month=6, day=8)

    date = start
    today = datetime.now()
    utc = pytz.UTC
    date = utc.localize(date)
    x = utc.localize(datetime.now())
    n_count = len(n)
    plain_list = []
    #while date.date() < today.date():
    while date.date() < end:
        full_duration = timedelta(microseconds=0)
        for i1 in n:
            duration = timedelta(microseconds=0)
            stops = Eq_stoptime.objects.filter(eq_id=i1.eq_id)
            for stop in stops:
                if (stop.start_time != None) and (stop.stop_time >= date) and (stop.stop_time <= date + step):
                    if stop.stop_time.date() == stop.start_time.date():
                        duration = stop.start_time - stop.stop_time
                    else:
                        duration = stop.shift_end - stop.stop_time
                        cancel = False
                        i_date = stop.stop_time + timedelta(hours=24)
                        while cancel == False:
                            if (i_date.date() == stop.start_time.date()):
                                j = stop.start_time - stop.shift_start
                            else:
                                if datetime.isoweekday(i_date.date()) < 6:
                                    j = timedelta(hours=8)
                                else:
                                    j = timedelta(seconds=0)
                            duration = duration + j
                            if (i_date.date() == stop.start_time.date()) or (i_date.date() >= date.date() + step):
                                cancel = True
                            i_date = i_date + timedelta(hours=24)
                elif (stop.start_time != None) and (stop.stop_time <= date) and (stop.start_time >= date + step):
                    duration = timedelta(hours=40)
                elif (stop.start_time != None) and (stop.stop_time < date) and (stop.start_time >= date) and (stop.start_time <= date + step):
                    cancel = False
                    i_date = date
                    while cancel == False:
                        if (i_date.date() == stop.start_time.date()):
                            j = stop.start_time - stop.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                j = timedelta(hours=8)
                            else:
                                j = timedelta(seconds=0)
                        duration = duration + j
                        if (i_date.date() == stop.start_time.date()) or (i_date.date() >= date.date() + step):
                            cancel = True
                        i_date = i_date + timedelta(hours=24)
                elif (stop.start_time == None):
                    if (stop.stop_time >= date) and (stop.stop_time <= date + step):
                        if stop.stop_time.date() == datetime.now().date():
                            duration = x - stop.stop_time
                        else:
                            duration = stop.shift_end - stop.stop_time
                            cancel = False
                            i_date = stop.stop_time + timedelta(hours=24)
                            while cancel == False:
                                if (i_date.date() == datetime.now().date()):

                                    j = x - stop.shift_start
                                else:
                                    if datetime.isoweekday(i_date.date()) < 6:
                                        j = timedelta(hours=8)
                                    else:
                                        j = timedelta(seconds=0)
                                duration = duration + j
                                if (i_date.date() == datetime.now().date()) or (i_date.date() >= date.date() + step):
                                    cancel = True
                                i_date = i_date + timedelta(hours=24)


                full_duration = full_duration + duration
        plain_list.append(full_duration.total_seconds() / 3600)
        date = date + step

    date = start
    today = datetime.now()
    utc = pytz.UTC
    date = utc.localize(date)
    maintenance_list = []
    expected_time_list = []
    dates = []
    while date.date() < end:
        full_duration_to = timedelta(microseconds=0)
        for j1 in n:
            duration_to = timedelta(microseconds=0)
            maints = Maintenance.objects.filter(eq_id=j1.eq_id)
            expected_time = 0
            for maint in maints:
                if (maint.start_time >= date) and (maint.start_time <= date + step):
                    if (maint.end_time != None) and (maint.start_time.date() == maint.end_time.date()):
                        duration_to = maint.end_time - maint.start_time
                    elif maint.end_time != None:
                        duration_to = maint.shift_end - maint.start_time
                        cancel = False
                        i_date = maint.start_time + timedelta(hours=24)
                        while cancel == False:
                            if (i_date.date() == maint.end_time.date()):
                                j = maint.end_time - maint.shift_start
                            else:
                                if datetime.isoweekday(i_date.date()) < 6:
                                    j = timedelta(hours=8)
                                else:
                                    j = timedelta(seconds=0)
                            duration_to = duration_to + j
                            if (i_date.date() == maint.end_time.date()) or (i_date.date() >= date.date() + step):
                                cancel = True
                            i_date = i_date + timedelta(hours=24)
                full_duration_to = full_duration_to + duration_to
                expected_time = expected_time + maint.expected_time
        maintenance_list.append(full_duration_to.total_seconds() / 3600)
        expected_time_list.append(expected_time)
        dates.append(date)
        date = date + step

    kpi_list = []
    for i in range(len(plain_list)):

        mean = ((n_count * 40 - expected_time_list[i]) - plain_list[i] - (maintenance_list[i] - expected_time_list[i])) / (n_count * 40 - expected_time_list[i])

        kpi_list.append(round(mean, 4))

    return plain_list, maintenance_list, expected_time_list, n_count * 40, kpi_list, dates

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
    for doer in doers:
        doer_full = Employees.objects.get(employee_id=doer)
        #doer_id = doer_full.tg_id
        send_message.send_message_to(doer_full.tg_id, to_id)

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

def period_queries_and_to(s1, s2):
    utc = pytz.UTC

    try:
        period_start = datetime(year=s1[0], month=s1[1], day=s1[2])
        period_end = datetime(year=s2[0], month=s2[1], day=s2[2])
    except:
        pass
    period_start = utc.localize(period_start)
    period_end = utc.localize(period_end)
    #today = datetime.today()
    #weekday = today.weekday()
    #start_delta = timedelta(days=weekday, weeks=1)
    #last_week_start = today - start_delta - timedelta(days=1)
    #last_week_end = last_week_start + timedelta(days=4)
    queries_ids = []
    to_ids = []
    n = Queries.objects.all()
    for i in n:
        if (i.stop_time is not None) and period_end.date() >= i.stop_time.date() >= period_start.date():
            queries_ids.append(i.query_id)
        elif i.query_status == 'В процессе' and i.post_time.date() <= period_end.date():
            queries_ids.append(i.query_id)
        elif i.query_status == 'Приостановлена' and i.post_time.date() <= period_end.date():
            queries_ids.append(i.query_id)
        elif (i.stop_time is not None) and i.stop_time.date() >= period_end.date() >= i.post_time.date():
            queries_ids.append(i.query_id)

    m = Maintenance.objects.all()
    for i in m:
        if i.end_time is not None and period_end.date() >= i.end_time.date() >= period_start.date():
            to_ids.append(i.id)
        elif i.status == 'В процессе' and i.start_time.date() <= period_end.date():
            to_ids.append(i.id)
        elif i.end_time is not None and i.start_time.date() <= period_end.date() <= i.end_time.date():
            to_ids.append(i.id)
    return queries_ids, to_ids






def top10_all_lastweek(equipment):
    pairs = []
    today = datetime.today()
    weekday = today.weekday()
    start_delta = timedelta(days=weekday, weeks=1)
    last_week_start = today - start_delta
    last_week_end = last_week_start + timedelta(days=4)
    utc = pytz.UTC
    last_week_start = utc.localize(last_week_start)
    last_week_end = utc.localize(last_week_end)

    for i1 in equipment:
        n = Eq_stoptime.objects.filter(eq_id=i1.eq_id)
        duration = timedelta(microseconds=0)
        full_duration = timedelta(microseconds=0)
        duration_to = timedelta(microseconds=0)
        full_duration_to = timedelta(microseconds=0)
        shifts = i1.shift
        for i in n:
            i.now = datetime.now()
            i.save()
            if i.start_time == None:
                i.start_time = datetime.now()
                w = 1
                i.save()
        n = Eq_stoptime.objects.filter(eq_id=i1.eq_id)  # по новой получаем список, так как он изменился
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
        n = Eq_stoptime.objects.filter(eq_id=i1.eq_id)  # по новой получаем список, так как он изменился
        for i in n:
            if i.stop_time >= last_week_start and i.start_time <= last_week_end:
                if i.stop_time.date() == i.start_time.date():  # если заявка начата и выполнена в 1 день
                    duration = i.start_time - i.stop_time
                else:  # если нет, то сюда
                    duration = i.shift_end - i.stop_time
                    stop = False
                    i_date = i.stop_time + timedelta(hours=24)
                    while stop == False:
                        if i_date.date() == i.start_time.date():
                            j = i.start_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                # j = i.shift_end - i.start_time
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration = duration + j
                        if i_date.date() == i.start_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
            elif (i.stop_time >= last_week_start and i.stop_time <= last_week_end) and i.start_time > last_week_end:
                duration = i.shift_end - i.stop_time
                stop = False
                i_date = i.stop_time + timedelta(hours=24)
                while stop == False:
                    if datetime.isoweekday(i_date.date()) < 6:
                        j = timedelta(hours=8) * shifts
                        duration = duration + j
                    else:
                        stop = True
                    i_date = i_date + timedelta(hours=24)
            elif (i.start_time >= last_week_start and i.start_time <= last_week_end) and i.stop_time < last_week_start:
                if i.start_time.date() == last_week_start.date():
                    duration = i.start_time - i.shift_start
                else:
                    stop = False
                    i_date = last_week_start
                    while stop == False:
                        if i_date.date() == i.start_time.date():
                            j = i.start_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration = duration + j
                        if i_date.date() == i.start_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
            elif (i.stop_time < last_week_start and i.start_time > last_week_end):
                duration = timedelta(hours=40)
            full_duration = full_duration + duration

        m = Maintenance.objects.filter(eq_id=i1.eq_id, status='В процессе')
        for i in m:
            i.end_time = datetime.now()
            i.save()

        #Item.objects.filter(Q(creator=owner) | Q(moderated=False))
        m = Maintenance.objects.filter(Q(eq_id=i1.eq_id, status='Завершено') | Q(eq_id=i1.eq_id, status='В процессе'))
        for i in m:
            if i.start_time >= last_week_start and i.end_time <= last_week_end:
                if i.start_time.date() == i.end_time.date():  # если заявка начата и выполнена в 1 день
                    duration_to = i.end_time - i.start_time
                else:  # если нет, то сюда
                    duration_to = i.shift_end - i.start_time
                    stop = False
                    i_date = i.start_time + timedelta(hours=24)
                    while stop == False:
                        if i_date.date() == i.end_time.date():
                            j = i.end_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                # j = i.shift_end - i.start_time
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration_to = duration_to + j
                        if i_date.date() == i.end_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
            elif (i.start_time >= last_week_start and i.start_time <= last_week_end) and i.end_time > last_week_end:
                duration_to = i.shift_end - i.start_time
                stop = False
                i_date = i.end_time + timedelta(hours=24)
                while stop == False:
                    if datetime.isoweekday(i_date.date()) < 6:
                        j = timedelta(hours=8) * shifts
                        duration_to = duration_to + j
                    else:
                        stop = True
                    i_date = i_date + timedelta(hours=24)
            elif (i.end_time >= last_week_start and i.end_time <= last_week_end) and i.start_time < last_week_start:
                if i.end_time.date() == last_week_start.date():
                    duration_to = i.end_time - i.shift_start
                else:
                    stop = False
                    i_date = last_week_start
                    while stop == False:
                        if i_date.date() == i.end_time.date():
                            j = i.end_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration_to = duration_to + j
                        if i_date.date() == i.end_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
            elif (i.start_time < last_week_start and i.end_time > last_week_end):
                duration_to = timedelta(hours=40)
            full_duration_to = full_duration_to + duration_to

        m = Maintenance.objects.filter(eq_id=i1.eq_id, status='В процессе')
        for i in m:
            i.end_time = None
            i.save()



        n = list(Eq_stoptime.objects.filter(eq_id=i1.eq_id))
        try:
            if w == 1:  # стирает добавленное время "Сейчас", чтобы бд была в том же состоянии
                i = n[-1]
                i.start_time = None
                i.save()
                w = 0
        except:
            pass
        sum = full_duration.total_seconds() + full_duration_to.total_seconds()
        pair = (i1.eq_name, full_duration.total_seconds() / 3600, full_duration_to.total_seconds() / 3600, shifts, i1.invnum, sum)
        pairs.append(pair)
    pairs = sorted(pairs, key=lambda x: x[5])  # сортировка по увеличению дней в простое
    pairs.reverse()
    pairs = pairs[:10]  # обрезка до 10 штук
    names = []
    means = []
    means_to = []
    sh = []
    invnum = []
    for j in pairs:
        names.append(j[0])
        means.append(j[1])
        means_to.append(j[2])
        sh.append(j[3])
        invnum.append(j[4])
    return names, means, means_to, sh, invnum

def top10_last_week(equipment):
    pairs = []
    today = datetime.today()
    weekday = today.weekday()
    start_delta = timedelta(days=weekday, weeks=1)
    last_week_start = today - start_delta
    last_week_end = last_week_start + timedelta(days=4)
    utc=pytz.UTC
    last_week_start = utc.localize(last_week_start)
    last_week_end = utc.localize(last_week_end)

    for i1 in equipment:
        n = Eq_stoptime.objects.filter(eq_id=i1.eq_id)
        duration = timedelta(microseconds=0)
        full_duration = timedelta(microseconds=0)
        shifts = i1.shift
        for i in n:
            i.now = datetime.now()
            i.save()
            if i.start_time == None:
                i.start_time = datetime.now()
                w = 1
                i.save()
        n = Eq_stoptime.objects.filter(eq_id=i1.eq_id)  # по новой получаем список, так как он изменился
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
        n = Eq_stoptime.objects.filter(eq_id=i1.eq_id)  # по новой получаем список, так как он изменился
        for i in n:
            if i.stop_time >= last_week_start and i.start_time <= last_week_end:
                if i.stop_time.date() == i.start_time.date(): # если заявка начата и выполнена в 1 день
                    duration = i.start_time - i.stop_time
                else:  # если нет, то сюда
                    duration = i.shift_end - i.stop_time
                    stop = False
                    i_date = i.stop_time + timedelta(hours=24)
                    while stop == False:
                        if i_date.date() == i.start_time.date():
                            j = i.start_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                # j = i.shift_end - i.start_time
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration = duration + j
                        if i_date.date() == i.start_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
            elif (i.stop_time >= last_week_start and i.stop_time <= last_week_end) and i.start_time > last_week_end:
                duration = i.shift_end - i.stop_time
                stop = False
                i_date = i.stop_time + timedelta(hours=24)
                while stop == False:
                    if datetime.isoweekday(i_date.date()) < 6:
                        j = timedelta(hours=8) * shifts
                        duration = duration + j
                    else:
                        stop = True
                    i_date = i_date + timedelta(hours=24)
            elif (i.start_time >= last_week_start and i.start_time <= last_week_end) and i.stop_time < last_week_start:
                if i.start_time.date() == last_week_start.date():
                    duration = i.start_time - i.shift_start
                else:
                    stop = False
                    i_date = last_week_start
                    while stop == False:
                        if i_date.date() == i.start_time.date():
                            j = i.start_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration = duration + j
                        if i_date.date() == i.start_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
            elif (i.stop_time < last_week_start and i.start_time > last_week_end):
                duration = timedelta(hours=40)

            full_duration = full_duration + duration
        n = list(Eq_stoptime.objects.filter(eq_id=i1.eq_id))
        try:
            if w == 1:  # стирает добавленное время "Сейчас", чтобы бд была в том же состоянии
                i = n[-1]
                i.start_time = None
                i.save()
                w = 0
        except:
            pass
        pair = (i1.eq_name, full_duration.total_seconds() / 3600, shifts, i1.invnum)
        pairs.append(pair)
    pairs = sorted(pairs, key=lambda x: x[1])  # сортировка по увеличению дней в простое
    pairs.reverse()
    pairs = pairs[:10]  # обрезка до 10 штук
    names = []
    means = []
    sh = []
    invnum = []
    for j in pairs:
        names.append(j[0])
        means.append(j[1])
        sh.append(j[2])
        invnum.append(j[3])
    return names, means, sh, invnum

def top10(equipment):
    pairs = []
    for i1 in equipment:
        shifts = i1.shift
        eq_id = i1.eq_id
        n = Eq_stoptime.objects.filter(eq_id=eq_id)  # блок высчитывает время простоя
        duration = timedelta(microseconds=0)  # он добавляет в бд текущее время, а потом удаляет его
        full_duration = timedelta(microseconds=0)
        for i in n:
            i.now = datetime.now()
            i.save()
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
        for i in n:                                      # главное тело подсчета простоя.
            if i.stop_time.date() == i.start_time.date():   #если заявка подана и выполнена в 1 день, то сюда
                duration = i.start_time - i.stop_time
            else:                                           #если нет, то сюда
                duration = i.shift_end - i.stop_time
                stop = False
                i_date = i.stop_time + timedelta(hours=24)
                while stop == False:
                    if i_date.date() == i.start_time.date():
                        j = i.start_time - i.shift_start
                    else:
                        if datetime.isoweekday(i_date.date()) < 6:
                            #j = i.shift_end - i.start_time
                            j = timedelta(hours=8) * shifts
                        else:
                            j = timedelta(seconds=0)
                    duration = duration + j
                    if i_date.date() == i.start_time.date():
                        stop = True
                    i_date = i_date + timedelta(hours=24)
            full_duration = full_duration + duration

        n = list(Eq_stoptime.objects.filter(eq_id=eq_id))
        try:
            if w == 1:                                  #стирает добавленное время "Сейчас", чтобы бд была в том же состоянии
                i = n[-1]
                i.start_time = None
                i.save()
                w = 0
        except:
            pass
        pair = (i1.eq_name, full_duration.total_seconds() / 3600, shifts, i1.invnum)
        pairs.append(pair)
    pairs = sorted(pairs, key=lambda x: x[1])  # сортировка по увеличению дней в простое
    pairs.reverse()
    pairs = pairs[:10]  # обрезка до 10 штук
    names = []
    means = []
    sh = []
    invnum = []
    for j in pairs:
        names.append(j[0])
        means.append(j[1])
        sh.append(j[2])
        invnum.append(j[3])
    return names, means, sh, invnum

def top10_month(equipment):
    today = datetime.now()  # топ 10 по простою за месяц
    this_month = today.month
    this_year = today.year
    stops = Eq_stoptime.objects.all()
    for q1 in stops:
        q1.month_start = datetime(this_year, this_month, 1, 7)
        q1.save()
    pairs_m = []
    for j1 in equipment:
        shifts = j1.shift
        eq_id = j1.eq_id
        n = Eq_stoptime.objects.filter(eq_id=eq_id)
        duration = timedelta(microseconds=0)
        full_duration = timedelta(microseconds=0)
        for i in n:
            if i.start_time == None:
                i.start_time = datetime.now()
                i.save()
                w = 1
        n = Eq_stoptime.objects.filter(eq_id=eq_id)
        for i in n:
            if i.stop_time.month == this_month and i.start_time.month == this_month:
                if i.stop_time.date() == i.start_time.date():
                    duration = i.start_time - i.stop_time
                else:
                    duration = i.shift_end - i.stop_time
                    stop = False
                    i_date = i.stop_time + timedelta(hours=24)
                    while stop == False:
                        if i_date.date() == i.start_time.date():
                            j = i.start_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                # j = i.shift_end - i.start_time
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration = duration + j
                        if i_date.date() == i.start_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
            elif i.start_time.month == this_month:
                if i.start_time.day == datetime(this_year, this_month, 1).day:
                    j = i.start_time - i.shift_start
                else:
                    duration = i.shift_end - i.stop_time
                    stop = False
                    i_date = datetime(this_year, this_month, 2)
                    while stop == False:
                        if i_date.date() == i.start_time.date():
                            j = i.start_time - i.shift_start
                            stop = True
                        else:
                            if datetime.isoweekday(i_date) < 6:
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration = duration + j
                        if i_date.date() == i.start_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
                duration = duration + j
            full_duration = full_duration + duration


        n = list(Eq_stoptime.objects.filter(eq_id=eq_id))
        try:
            if w == 1:
                i = n[-1]
                i.start_time = None
                i.save()
                w = 0
        except:
            pass
        pair2 = (j1.eq_name, full_duration.total_seconds() / 3600, shifts, j1.invnum)
        pairs_m.append(pair2)
    pairs_m = sorted(pairs_m, key=lambda x: x[1])  # сортировка по увеличению дней в простое
    pairs_m.reverse()
    pairs_m = pairs_m[:10]  # обрезка до 10 штук
    names_m = []
    means_m = []
    sh_m = []
    invnum = []
    for j in pairs_m:
        names_m.append(j[0])
        means_m.append(j[1])
        sh_m.append(j[2])
        invnum.append(j[3])
    return names_m, means_m, sh_m, invnum

def top10_all(equipment):
    pairs = []
    for i1 in equipment:
        shifts = i1.shift
        eq_id = i1.eq_id
        n = Eq_stoptime.objects.filter(eq_id=eq_id)  # блок высчитывает время простоя
        m = Maintenance.objects.filter(eq_id=eq_id, status='Завершено')
        duration = timedelta(microseconds=0)  # он добавляет в бд текущее время, а потом удаляет его
        full_duration = timedelta(microseconds=0)
        duration_to = timedelta(microseconds=0)
        full_duration_to = timedelta(microseconds=0)
        for i in n:
            i.now = datetime.now()
            i.save()
            if i.start_time == None:
                i.start_time = datetime.now()
                w = 1
                i.save()

        n = Eq_stoptime.objects.filter(eq_id=eq_id)  # по новой получаем список, так как он изменился
        m = Maintenance.objects.filter(eq_id=eq_id, status='Завершено')
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
        for i in m:
            start_year = i.start_time.year
            start_month = i.start_time.month
            start_day = i.start_time.day
            end_year = i.end_time.year
            end_month = i.end_time.month
            end_day = i.end_time.day
            if shifts == 1:
                i.shift_end = datetime(start_year, start_month, start_day, 15)
            else:
                i.shift_end = datetime(start_year, start_month, start_day, 23)
            i.shift_start = datetime(end_year, end_month, end_day, 7)
            i.save()

        n = Eq_stoptime.objects.filter(eq_id=eq_id)  # по новой получаем список, так как он изменился
        m = Maintenance.objects.filter(eq_id=eq_id, status='Завершено')
        for i in n:  # главное тело подсчета простоя.
            if i.stop_time.date() == i.start_time.date():  # если заявка подана и выполнена в 1 день, то сюда
                duration = i.start_time - i.stop_time
            else:  # если нет, то сюда
                duration = i.shift_end - i.stop_time
                stop = False
                i_date = i.stop_time + timedelta(hours=24)
                while stop == False:
                    if i_date.date() == i.start_time.date():
                        j = i.start_time - i.shift_start
                    else:
                        if datetime.isoweekday(i_date.date()) < 6:
                            # j = i.shift_end - i.start_time
                            j = timedelta(hours=8) * shifts
                        else:
                            j = timedelta(seconds=0)
                    duration = duration + j
                    if i_date.date() == i.start_time.date():
                        stop = True
                    i_date = i_date + timedelta(hours=24)
            full_duration = full_duration + duration

        for i in m:  # главное тело подсчета простоя.
            if i.start_time.date() == i.end_time.date():  # если ТО выполнена в 1 день, то сюда
                duration_to = i.end_time - i.start_time
            else:  # если нет, то сюда
                duration_to = i.shift_end - i.start_time
                stop = False
                i_date = i.start_time + timedelta(hours=24)
                while stop == False:
                    if i_date.date() == i.end_time.date():
                        j = i.end_time - i.shift_start
                    else:
                        if datetime.isoweekday(i_date.date()) < 6:
                            # j = i.shift_end - i.start_time
                            j = timedelta(hours=8) * shifts
                        else:
                            j = timedelta(seconds=0)
                    duration_to = duration_to + j
                    if i_date.date() == i.end_time.date():
                        stop = True
                    i_date = i_date + timedelta(hours=24)
            full_duration_to = full_duration_to + duration_to

        m = Maintenance.objects.filter(eq_id=eq_id, status='В процессе')
        for i in m:
            i.end_time = datetime.now()
            i.shift_start = datetime(year=datetime.today().year, month=datetime.today().month, day=datetime.today().day, hour=7)
            i.shift_end = datetime(year=i.start_time.year, month=i.start_time.month, day=i.start_time.day, hour=15)
            i.save()
        m = Maintenance.objects.filter(eq_id=eq_id, status='В процессе')

        for i in m:  # главное тело подсчета простоя.
            if i.start_time.date() == i.end_time.date():  # если ТО выполнена в 1 день, то сюда
                duration_to = i.end_time - i.start_time
            else:  # если нет, то сюда
                duration_to = i.shift_end - i.start_time
                stop = False
                i_date = i.start_time + timedelta(hours=24)
                while stop == False:
                    if i_date.date() == i.end_time.date():
                        j = i.end_time - i.shift_start
                    else:
                        if datetime.isoweekday(i_date.date()) < 6:
                            # j = i.shift_end - i.start_time
                            j = timedelta(hours=8) * shifts
                        else:
                            j = timedelta(seconds=0)
                    duration_to = duration_to + j
                    if i_date.date() == i.end_time.date():
                        stop = True
                    i_date = i_date + timedelta(hours=24)
            full_duration_to = full_duration_to + duration_to
            i.end_time = None
            i.save()



        n = list(Eq_stoptime.objects.filter(eq_id=eq_id))
        try:
            if w == 1:  # стирает добавленное время "Сейчас", чтобы бд была в том же состоянии
                i = n[-1]
                i.start_time = None
                i.save()
                w = 0
        except: pass

        sum = full_duration.total_seconds() + full_duration_to.total_seconds()
        pair = (i1.eq_name, full_duration.total_seconds() / 3600, full_duration_to.total_seconds() / 3600, shifts, i1.invnum, sum)
        pairs.append(pair)
    pairs = sorted(pairs, key=lambda x: x[5])  # сортировка по увеличению дней в простое
    pairs.reverse()
    pairs = pairs[:15]  # обрезка до 10 штук
    names = []
    means = []
    means_to = []
    sh = []
    invnum = []
    for j in pairs:
        names.append(j[0])
        means.append(j[1])
        means_to.append(j[2])
        sh.append(j[3])
        invnum.append(j[4])
    return names, means, means_to, sh, invnum

def top10_all_month(equipment):
    today = datetime.now()  # топ 10 по простою за месяц
    this_month = today.month
    this_year = today.year
    stops = Eq_stoptime.objects.all()
    for q1 in stops:
        q1.month_start = datetime(this_year, this_month, 1, 7)
        q1.save()
    maints = Maintenance.objects.all()
    for q2 in maints:
        q2.month_start = datetime(this_year, this_month, 1, 7)
        q2.save()
    pairs_m = []
    full_full_duration = timedelta(microseconds=0)
    full_full_duration_to = timedelta(microseconds=0)
    for j1 in equipment:
        shifts = j1.shift
        eq_id = j1.eq_id
        n = Eq_stoptime.objects.filter(eq_id=eq_id)
        duration = timedelta(microseconds=0)
        full_duration = timedelta(microseconds=0)
        duration_to = timedelta(microseconds=0)
        full_duration_to = timedelta(microseconds=0)
        expected_time = 0
        for i in n:
            if i.start_time == None:
                i.start_time = datetime.now()
                i.save()
                w = 1
        n = Eq_stoptime.objects.filter(eq_id=eq_id)
        for i in n:
            if i.stop_time.month == this_month and i.start_time.month == this_month:
                if i.stop_time.date() == i.start_time.date():
                    duration = i.start_time - i.stop_time
                else:
                    duration = i.shift_end - i.stop_time
                    stop = False
                    i_date = i.stop_time + timedelta(hours=24)
                    while stop == False:
                        if i_date.date() == i.start_time.date():
                            j = i.start_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                # j = i.shift_end - i.start_time
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration = duration + j
                        if i_date.date() == i.start_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
            elif i.start_time.month == this_month and i.stop_time.month != this_month:
                if i.start_time.day == datetime(this_year, this_month, 1).day:
                    j = i.start_time - i.shift_start
                else:
                    #duration = i.shift_end - i.stop_time
                    stop = False
                    i_date = i.stop_time + timedelta(hours=24)
                    while stop == False:
                        if (i_date.date() == i.start_time.date()) and (datetime.isoweekday(i_date.date()) < 6):
                            j = i.start_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                # j = i.shift_end - i.start_time
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration = duration + j
                        if i_date.date() == i.start_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
                #duration = duration + j
            full_duration = full_duration + duration
        m = Maintenance.objects.filter(eq_id=eq_id, status='Завершено')
        for i in m:
            if i.start_time.month == this_month and i.end_time.month == this_month:
                if i.start_time.date() == i.end_time.date():
                    duration_to = i.end_time - i.start_time
                else:
                    duration_to = i.shift_end - i.start_time
                    stop = False
                    i_date = i.start_time + timedelta(hours=24)
                    while stop == False:
                        if i_date.date() == i.end_time.date():
                            j = i.end_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                # j = i.shift_end - i.start_time
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration_to = duration_to + j
                        if i_date.date() == i.end_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
            elif i.end_time.month == this_month:
                if i.end_time.day == datetime(this_year, this_month, 1).day:
                    j = i.end_time - i.shift_start
                else:
                    duration_to = i.shift_end - i.start_time
                    stop = False
                    i_date = datetime(this_year, this_month, 2)
                    while stop == False:
                        if i_date.date() == i.end_time.date():
                            j = i.end_time - i.shift_start

                        else:
                            if datetime.isoweekday(i_date) < 6:
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration_to = duration_to + j
                        if i_date.date() == i.end_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
                duration_to = duration_to + j
            full_duration_to = full_duration_to + duration_to
            expected_time = expected_time + i.expected_time

        m = Maintenance.objects.filter(eq_id=eq_id, status='В процессе')
        for i in m:
            i.end_time = datetime.now()
            i.save()
        m = Maintenance.objects.filter(eq_id=eq_id, status='В процессе')
        for i in m:
            if i.start_time.month == this_month and i.end_time.month == this_month:
                if i.start_time.date() == i.end_time.date():
                    duration_to = i.end_time - i.start_time
                else:
                    duration_to = i.shift_end - i.start_time
                    stop = False
                    i_date = i.start_time + timedelta(hours=24)
                    while stop == False:
                        if i_date.date() == i.end_time.date():
                            j = i.end_time - i.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                # j = i.shift_end - i.start_time
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration_to = duration_to + j
                        if i_date.date() == i.end_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
            elif i.end_time.month == this_month:
                if i.end_time.day == datetime(this_year, this_month, 1).day:
                    j = i.end_time - i.shift_start
                else:
                    duration_to = i.shift_end - i.start_time
                    stop = False
                    i_date = datetime(this_year, this_month, 2)
                    while stop == False:
                        if i_date.date() == i.end_time.date():
                            j = i.end_time - i.shift_start
                            stop = True
                        else:
                            if datetime.isoweekday(i_date) < 6:
                                j = timedelta(hours=8) * shifts
                            else:
                                j = timedelta(seconds=0)
                        duration_to = duration_to + j
                        if i_date.date() == i.end_time.date():
                            stop = True
                        i_date = i_date + timedelta(hours=24)
                duration_to = duration_to + j
            full_duration_to = full_duration_to + duration_to
            i.end_time = None
            i.save()
            expected_time = expected_time + i.expected_time
        full_full_duration = full_full_duration + full_duration
        full_full_duration_to = full_full_duration_to + full_duration_to

        n = list(Eq_stoptime.objects.filter(eq_id=eq_id))
        try:
            if w == 1:
                i = n[-1]
                i.start_time = None
                i.save()
                w = 0
        except:
            pass
        sum = full_duration.total_seconds() + full_duration_to.total_seconds()

        pair2 = (j1.eq_name, full_duration.total_seconds() / 3600, full_duration_to.total_seconds() / 3600, shifts, j1.invnum, sum, expected_time)
        pairs_m.append(pair2)
    pairs_m = sorted(pairs_m, key=lambda x: x[5])  # сортировка по увеличению дней в простое
    pairs_m.reverse()
    pairs_m = pairs_m[:15]  # обрезка до 10 штук
    names_m = []
    means_m = []
    means_m_to = []
    sh_m = []
    invnum = []
    expected_times = []
    for j in pairs_m:
        names_m.append(j[0])
        means_m.append(j[1])
        means_m_to.append(j[2])
        sh_m.append(j[3])
        invnum.append(j[4])
        expected_times.append(j[6])
    return names_m, means_m, means_m_to, sh_m, invnum, full_full_duration.total_seconds() / 3600, full_full_duration_to.total_seconds() / 3600, expected_times

def last_week_queries_and_to():
    today = datetime.today()
    weekday = today.weekday()
    start_delta = timedelta(days=weekday, weeks=1)
    last_week_start = today - start_delta - timedelta(days=1)
    last_week_end = last_week_start + timedelta(days=4)
    utc = pytz.UTC
    last_week_start = utc.localize(last_week_start)
    last_week_end = utc.localize(last_week_end)
    queries_ids = []
    to_ids = []
    n = Queries.objects.all()
    for i in n:
        if (i.stop_time is not None) and last_week_end >= i.stop_time >= last_week_start:
            queries_ids.append(i.query_id)
        elif i.query_status == 'В процессе' and i.post_time <= last_week_end:
            queries_ids.append(i.query_id)
        elif i.query_status == 'Приостановлена' and i.post_time <= last_week_end:
            queries_ids.append(i.query_id)
        elif (i.stop_time is not None) and i.stop_time >= last_week_end >= i.post_time:
            queries_ids.append(i.query_id)

    m = Maintenance.objects.all()
    for i in m:
        if i.end_time is not None and last_week_end >= i.end_time >= last_week_start:
            to_ids.append(i.id)
        elif i.status == 'В процессе' and i.start_time <= last_week_end:
            to_ids.append(i.id)
        elif i.end_time is not None and i.start_time <= last_week_end <= i.end_time:
            to_ids.append(i.id)
    return queries_ids, to_ids

