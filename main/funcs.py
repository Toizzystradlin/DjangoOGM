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

def to(area, s1, s2):
    utc = pytz.UTC
    period_start = datetime(year=s1[0], month=s1[1], day=s1[2])
    period_end = datetime(year=s2[0], month=s2[1], day=s2[2])
    period_start = utc.localize(period_start)
    period_end = utc.localize(period_end)
    pairs = []
    maints = Maintenance.objects.all()
    maints = maints.exclude(status='Новое')
    for maint in maints:
        if maint.end_time is not None:
            end_of_maint = maint.end_time
        else:
            end_of_maint = utc.localize(datetime.now())
        maint.shift_start = datetime(year=end_of_maint.year, month=end_of_maint.month, day=end_of_maint.day,
                                     hour=7)
        maint.shift_end = datetime(year=end_of_maint.year, month=end_of_maint.month, day=end_of_maint.day,
                                   hour=15)
        maint.save()

    maints = Maintenance.objects.all()
    maints = maints.exclude(status='Новое')
    for maint in maints:
        duration_to = timedelta(microseconds=0)
        eq = Equipment.objects.get(eq_id=maint.eq_id)
        if eq.area != area and area != 'Все участки':
            pass
        elif eq.area == area or area == 'Все участки':
            eq_name = eq.eq_name
            if maint.end_time is not None:
                end_time = maint.end_time
            else:
                end_time = utc.localize(datetime.now())
            if (maint.start_time.date() == end_time.date()) and (
                    period_start.date() <= maint.start_time.date() <= period_end.date()):
                duration_to = end_time - maint.start_time
                pair = (eq_name, duration_to.total_seconds() / 3600, maint.expected_time)
                pairs.append(pair)
            elif period_start.date() <= maint.start_time.date() <= period_end.date():
                duration_to = maint.shift_end - maint.start_time
                cancel = False
                i_date = maint.start_time + timedelta(hours=24)
                while cancel == False:
                    if (i_date.date() == end_time.date()):
                        j = end_time - maint.shift_start
                    else:
                        if datetime.isoweekday(i_date.date()) < 6:
                            j = timedelta(hours=8)
                        else:
                            j = timedelta(seconds=0)
                    duration_to = duration_to + j
                    if (i_date.date() == end_time.date()) or (i_date.date() >= period_end.date()):
                        cancel = True
                    i_date = i_date + timedelta(hours=24)
                pair = (eq_name, duration_to.total_seconds() / 3600, maint.expected_time)
                pairs.append(pair)
            elif (maint.start_time.date() < period_start.date()) and (end_time.date() >= period_start.date()):
                cancel = False
                i_date = period_start
                while cancel == False:
                    if (i_date.date() == end_time.date()):
                        j = end_time - maint.shift_start
                    else:
                        if datetime.isoweekday(i_date.date()) < 6:
                            j = timedelta(hours=8)
                        else:
                            j = timedelta(seconds=0)
                    duration_to = duration_to + j
                    if (i_date.date() == end_time.date()) or (i_date.date() >= period_end.date()):
                        cancel = True
                    i_date = i_date + timedelta(hours=24)
                pair = (eq_name, duration_to.total_seconds() / 3600, maint.expected_time)
                pairs.append(pair)
    return pairs

def plain_period(equipment, s1, s2):
    for i1 in equipment:
        shifts = i1.shift
        eq_id = i1.eq_id
        n = Eq_stoptime.objects.filter(eq_id=eq_id)  # по новой получаем список, так как он изменился
        for i in n:
            start_year = i.stop_time.year
            start_month = i.stop_time.month
            start_day = i.stop_time.day
            try:
                end_year = i.start_time.year
                end_month = i.start_time.month
                end_day = i.start_time.day
            except:
                end_year = datetime.now().year
                end_month = datetime.now().month
                end_day = datetime.now().day
            if shifts == 1:
                i.shift_end = datetime(start_year, start_month, start_day, 15)
            else:
                i.shift_end = datetime(start_year, start_month, start_day, 23)
            try:
                i.shift_start = datetime(end_year, end_month, end_day, 7)
            except:
                pass
            i.save()


    utc = pytz.UTC
    period_start = datetime(year=s1[0], month=s1[1], day=s1[2])
    period_end = datetime(year=s2[0], month=s2[1], day=s2[2])
    pairs = []
    full_full_duration = timedelta(hours=0)
    full_full_duration_to = timedelta(hours=0)
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
        full_full_duration = full_full_duration + full_duration
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
        full_full_duration_to = full_full_duration_to + full_duration_to
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
    return names, means, means_to, invnum, full_full_duration.total_seconds() / 3600, full_full_duration_to.total_seconds() / 3600

def time_kpi(n, s1, s2, s3='day'):
    start = datetime(year=s1[0], month=s1[1], day=s1[2])
    end = datetime(year=s2[0], month=s2[1], day=s2[2])
    if s3 == 'day': step = timedelta(days=1)
    if s3 == 'week': step = timedelta(weeks=1)
    if s3 == 'month': step = timedelta(weeks=4)
    date = start
    utc = pytz.UTC
    date = utc.localize(date)
    n_count = len(n)
    plain_list = []
    while date.date() <= end.date():
        full_duration = timedelta(microseconds=0)
        for i1 in n:
            duration = timedelta(microseconds=0)
            stops = Eq_stoptime.objects.filter(eq_id=i1.eq_id)
            for stop in stops:
                if stop.start_time is not None:
                    start_time = stop.start_time
                else:
                    start_time = utc.localize(datetime.now())
                if (stop.stop_time >= date) and (stop.stop_time <= date + step):
                    if stop.stop_time.date() == start_time.date():
                        duration = start_time - stop.stop_time
                    else:
                        duration = stop.shift_end - stop.stop_time
                        cancel = False
                        i_date = stop.stop_time + timedelta(hours=24)
                        while cancel == False:
                            if (i_date.date() == start_time.date()):
                                j = start_time - stop.shift_start
                            else:
                                if datetime.isoweekday(i_date.date()) < 6:
                                    j = timedelta(hours=8)
                                else:
                                    j = timedelta(seconds=0)
                            duration = duration + j
                            if (i_date.date() == start_time.date()) or (i_date.date() > date.date() + step):
                                cancel = True
                            i_date = i_date + timedelta(hours=24)
                elif (stop.stop_time < date) and (start_time >= date + step):
                    duration = timedelta(hours=40)
                elif (stop.stop_time < date) and (start_time >= date) and (start_time <= date + step):
                    cancel = False
                    i_date = date
                    while cancel == False:
                        if (i_date.date() == start_time.date()):
                            j = start_time - stop.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                j = timedelta(hours=8)
                            else:
                                j = timedelta(seconds=0)
                        duration = duration + j
                        if (i_date.date() == start_time.date()) or (i_date.date() > date.date() + step):
                            cancel = True
                        i_date = i_date + timedelta(hours=24)
                full_duration = full_duration + duration
        plain_list.append(full_duration.total_seconds() / 3600)
        date = date + step

    date = start
    utc = pytz.UTC
    date = utc.localize(date)
    maintenance_list = []
    expected_time_list = []
    dates = []
    while date.date() <= end.date():
        full_duration_to = timedelta(microseconds=0)
        for j1 in n:
            duration_to = timedelta(microseconds=0)
            maints = Maintenance.objects.filter(eq_id=j1.eq_id)
            expected_time = 0
            for maint in maints:
                if maint.end_time is not None:
                    end_time = maint.end_time
                else:
                    end_time = utc.localize(datetime.now())
                if (maint.start_time >= date) and (maint.start_time <= date + step):
                    if (maint.start_time.date() == end_time.date()):
                        duration_to = end_time - maint.start_time
                    else:
                        duration_to = maint.shift_end - maint.start_time
                        cancel = False
                        i_date = maint.start_time + timedelta(hours=24)
                        while cancel == False:
                            if (i_date.date() == end_time.date()):
                                j = end_time - maint.shift_start
                            else:
                                if datetime.isoweekday(i_date.date()) < 6:
                                    j = timedelta(hours=8)
                                else:
                                    j = timedelta(seconds=0)
                            duration_to = duration_to + j
                            if (i_date.date() == end_time.date()) or (i_date.date() > date.date() + step):
                                cancel = True
                            i_date = i_date + timedelta(hours=24)
                elif (date > maint.start_time) and (end_time >= date + step):
                    duration_to = timedelta(hours=40)
                elif (maint.start_time < date) and (end_time >= date) and (end_time <= date + step):
                    cancel = False
                    i_date = date
                    while cancel == False:
                        if (i_date.date() == end_time.date()):
                            j = end_time - maint.shift_start
                        else:
                            if datetime.isoweekday(i_date.date()) < 6:
                                j = timedelta(hours=8)
                            else:
                                j = timedelta(seconds=0)
                        duration_to = duration_to + j
                        if (i_date.date() == end_time.date()) or (i_date.date() > date.date() + step):
                            cancel = True
                        i_date = i_date + timedelta(hours=24)
                full_duration_to = full_duration_to + duration_to
                expected_time = expected_time + maint.expected_time
        maintenance_list.append(full_duration_to.total_seconds() / 3600)
        expected_time_list.append(expected_time)
        dates.append(date)
        date = date + step

    kpi_list = []
    kpi_pairs = []
    for i in range(len(plain_list)):
        mean = ((n_count * 40 - expected_time_list[i]) - plain_list[i] - (maintenance_list[i] - expected_time_list[i])) / (n_count * 40 - expected_time_list[i])
        kpi_list.append(round(mean, 4))
        kpi_pair = (n_count * 40 - expected_time_list[i], plain_list[i] - (maintenance_list[i] - expected_time_list[i]), n_count * 40 - expected_time_list[i])
        kpi_pairs.append(kpi_pair)


    return plain_list, maintenance_list, expected_time_list, n_count * 40, kpi_list, dates, kpi_pairs

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
        time.sleep(0.5)

def appoint_doers_work(doers, work_id):
    doers_dict = {'doers': doers}
    doers_json = json.dumps(doers_dict)
    work = Unstated_works.objects.get(work_id=work_id)
    work.json_emp = doers_json
    work.save()
    for doer in doers:
        doer_work = Employees.objects.get(employee_id=doer)
        doer_id = doer_work.tg_id
        send_message.send_message_work(doer_id, work_id)

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

def period_queries_and_to(area, s1, s2):
    utc = pytz.UTC

    try:
        period_start = datetime(year=s1[0], month=s1[1], day=s1[2])
        period_end = datetime(year=s2[0], month=s2[1], day=s2[2])
    except:
        pass
    period_start = utc.localize(period_start)
    period_end = utc.localize(period_end)
    queries_ids = []
    to_ids = []
    u_ids = []
    n = Queries.objects.all()
    n_count = 0
    for i in n:
        eq = Equipment.objects.get(eq_id=i.eq_id)
        if eq.area != area and area != 'Все участки':
            pass
        elif eq.area == area or area == 'Все участки':
            if (i.stop_time is not None) and period_end.date() >= i.stop_time.date() >= period_start.date():
                queries_ids.append(i.query_id)
                n_count += 1
            elif i.query_status == 'В процессе' and i.post_time.date() <= period_end.date():
                queries_ids.append(i.query_id)
                n_count += 1
            elif i.query_status == 'Приостановлена' and i.post_time.date() <= period_end.date():
                queries_ids.append(i.query_id)
                n_count += 1
            elif (i.stop_time is not None) and i.stop_time.date() >= period_end.date() >= i.post_time.date():
                queries_ids.append(i.query_id)
                n_count += 1

    m = Maintenance.objects.all()
    m_count = 0
    m_process_count = 0
    to_done_count = 0
    for i in m:
        eq = Equipment.objects.get(eq_id=i.eq_id)
        if eq.area != area and area != 'Все участки':
            pass
        elif eq.area == area or area == 'Все участки':
            if i.end_time is not None and period_end.date() >= i.end_time.date() >= period_start.date():
                to_ids.append(i.id)
                m_count += 1
                to_done_count += 1
            elif i.status == 'В процессе' and i.start_time.date() <= period_end.date():
                to_ids.append(i.id)
                m_count += 1
                m_process_count += 1
            elif i.end_time is not None and i.start_time.date() <= period_end.date() <= i.end_time.date():
                to_ids.append(i.id)
                m_count += 1
            elif i.end_time is None and period_start.date() <= i.start_time.date() <= period_end.date():
                to_ids.append(i.id)
                m_count += 1

    u = Unstated_works.objects.all()
    u_count = 0
    try:
        for i in u:
            if i.stop_time is not None and period_end.date() >= i.stop_time.date() >= period_start.date():
                u_ids.append(i.work_id)
                u_count += 1
            elif i.query_status == 'В процессе' and i.start_time.date() <= period_end.date():
                u_ids.append(i.work_id)
                u_count += 1
            elif i.stop_time is not None and i.start_time.date() <= period_end.date() <= i.stop_time.date():
                u_ids.append(i.work_id)
                u_count += 1
    except: pass
    return queries_ids, to_ids, u_ids, n_count, m_count, u_count, to_done_count,  m_process_count

def employees_queries_and_works(employee_id, date1, date2):
    query_ids = []
    queries = Queries.objects.all()
    for query in queries:
        try:
            if (date2.date() > query.post_time.date() > date1.date()) or (date2.date() > query.stop_time.date() > date1.date()):
                emps_dict = json.loads(query.json_emp)
                doers = emps_dict['doers']
                for doer in doers:
                    if employee_id == int(doer):
                        query_ids.append(query.query_id)
        except: pass
    work_ids = []
    works = Unstated_works.objects.all()
    for work in works:
        try:
            if (date2.date() > work.post_time.date() > date1.date()) or (date2.date() > work.stop_time.date() > date1.date()):
                emps_dict = json.loads(work.json_emp)
                doers = emps_dict['doers']
                for doer in doers:
                    if employee_id == int(doer):
                        work_ids.append(work.work_id)
        except: pass
    to_ids = []
    maints = Maintenance.objects.all()
    maints = maints.exclude(end_time = None)
    for maint in maints:
        #try:
        if (date2.date() >= maint.end_time.date() >= date1.date()):
            emps_dict = json.loads(maint.employee_id)
            doers = emps_dict['doers']
            for doer in doers:
                if employee_id == int(doer):
                    to_ids.append(maint.id)
        #except: pass

    return query_ids, work_ids, to_ids

#def query_timeline(query_id):
#    with connection.cursor() as cursor:
#        cursor.execute("SELECT post_time, appoint_time, start_time, stop_time FROM queries WHERE query_id = %s", [query_id])
#        times = cursor.fetchone()
#        times = list(times)
#        if times[1] == None:
#            times[1] = datetime.now()
#
#
#        if times[0].date() == times[1].date():
#            new = times[1] - times[0]
#            new = new.total_seconds() / 3600
#        else:
#            shift_end = times[0].replace(hour=15, minute=30)
#            d1 = shift_end - times[0]
#            shift_start = times[1].replace(hour=7, minute=0)
#            d_last = times[1] - shift_start
#            delta = times[1] - times[0]
#
#            duration = timedelta(hours=0)
#            i_date = times[0] + timedelta(hours=24)
#
#            cancel = False
#            while cancel == False:
#                if i_date.date() == times[1].date():
#                    cancel = True
#                else:
#                    if datetime.isoweekday(i_date.date()) < 6:
#                        duration = duration + timedelta(hours=8)
#                i_date = i_date + timedelta(hours=24)
#            new = d1 + duration + d_last
#            new = new.total_seconds() / 3600
#
#
#        if times[2] != None:
#            if times[1].date() == times[2].date():
#                sent = times[2] - times[1]
#                sent = sent.total_seconds() / 3600
#            else:
#                shift_end = times[1].replace(hour=15, minute=30)
#                d1 = shift_end - times[1]
#                shift_start = times[2].replace(hour=7, minute=0)
#                d_last = times[2] - shift_start
#                delta = times[2] - times[0]
#                duration2 = timedelta(hours=0)
#                i_date = times[1] + timedelta(hours=24)
#                cancel = False
#                while cancel == False:
#                    if i_date.date() == times[2].date():
#                        cancel = True
#                    else:
#                        if datetime.isoweekday(i_date.date()) < 6:
#                            duration2 = duration2 + timedelta(hours=8)
#                    i_date = i_date + timedelta(hours=24)
#                sent = d1 + duration2 + d_last
#                sent = sent.total_seconds() / 3600
#        else:
#            sent = 0
#
#        if times[3] != None:
#            if times[2].date() == times[3].date():
#                process = times[3] - times[2]
#                process = process.total_seconds() / 3600
#            else:
#                shift_end = times[2].replace(hour=15, minute=30)
#                d1 = shift_end - times[2]
#                shift_start = times[3].replace(hour=7, minute=0)
#                d_last = times[3] - shift_start
#                delta = times[3] - times[0]
#                duration3 = timedelta(hours=0)
#                i_date = times[2] + timedelta(hours=24)
#                cancel = False
#                while cancel == False:
#                    if i_date.date() == times[3].date():
#                        cancel = True
#                    else:
#                        if datetime.isoweekday(i_date.date()) < 6:
#                            duration3 = duration2 + timedelta(hours=8)
#                    i_date = i_date + timedelta(hours=24)
#                process = d1 + duration3 + d_last
#                process = process.total_seconds() / 3600
#        else:
#            process = 0
#
#        return new, sent, process

def this_month_to_list(month):
    maints = Maintenance.objects.all()
    x = []
    y = []
    for m in maints:
        if ((m.plan_date.month == month and m.plan2_date == None) or (m.plan2_date != None and m.plan2_date.month == month)) and (m.status != 'Завершено'):
            x.append(m.id)
    for i in x:
        with connection.cursor() as cursor:
            cursor.execute("SELECT equipment.eq_name, equipment.invnum, equipment.eq_type, equipment.area, "
                           "maintenance.plan_date, maintenance.comment, maintenance.id, maintenance.status, maintenance.status2, maintenance.type FROM equipment JOIN "
                           "maintenance ON (equipment.eq_id = maintenance.eq_id) WHERE maintenance.id = %s", [i])
            res = cursor.fetchone()
        y.append(list(res))
    return y


