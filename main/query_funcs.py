from django.shortcuts import render, redirect
from .models import Queries, Equipment, Employees, Comment, Maintenance, Worktime, Eq_stoptime, Unstated_works
from datetime import datetime, timedelta, timezone
from django.db import connection
user_timezone_sql = '+03:00'


def change_time(request, query_id):
    query = Queries.objects.get(query_id=query_id)
    start_time = request.POST.get('start_datetime')
    stop_time = request.POST.get('stop_datetime')
    query.start_time = start_time
    query.stop_time = stop_time
    if query.appoint_time == None:
        query.appoint_time = query.post_time
    query.save()
    return redirect('/main/' + str(query_id))

def query_timeline(query_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT CONVERT_TZ(post_time, '+00:00', %s), CONVERT_TZ(appoint_time, '+00:00', %s), "
                       "CONVERT_TZ(start_time, '+00:00', %s), CONVERT_TZ(stop_time, '+00:00', %s) FROM queries WHERE "
                       "query_id = %s", [user_timezone_sql, user_timezone_sql, user_timezone_sql, user_timezone_sql, query_id])
        times = cursor.fetchone()
        times = list(times)
        if times[1] == None:
            times[1] = datetime.now()

        if times[0].date() == times[1].date():
            new = times[1] - times[0]
            new = new.total_seconds() / 3600
        else:
            shift_end = times[0].replace(hour=15, minute=30)
            d1 = shift_end - times[0]
            shift_start = times[1].replace(hour=7, minute=0)
            d_last = times[1] - shift_start
            delta = times[1] - times[0]

            duration = timedelta(hours=0)
            i_date = times[0] + timedelta(hours=24)

            cancel = False
            while cancel == False:
                if i_date.date() == times[1].date():
                    cancel = True
                else:
                    if datetime.isoweekday(i_date.date()) < 6:
                        duration = duration + timedelta(hours=8)
                i_date = i_date + timedelta(hours=24)
            new = d1 + duration + d_last
            new = new.total_seconds() / 3600


        if times[2] == None:
            times[2] = datetime.now()
        if times[1].date() == times[2].date():
            sent = times[2] - times[1]
            sent = sent.total_seconds() / 3600
        else:
            shift_end = times[1].replace(hour=15, minute=30)
            d1 = shift_end - times[1]
            shift_start = times[2].replace(hour=7, minute=0)
            d_last = times[2] - shift_start
            delta = times[2] - times[0]
            duration2 = timedelta(hours=0)
            i_date = times[1] + timedelta(hours=24)
            cancel = False
            while cancel == False:
                if i_date.date() == times[2].date():
                    cancel = True
                else:
                    if datetime.isoweekday(i_date.date()) < 6:
                        duration2 = duration2 + timedelta(hours=8)
                i_date = i_date + timedelta(hours=24)
            sent = d1 + duration2 + d_last
            sent = sent.total_seconds() / 3600

        if times[3] == None:
            times[3] = datetime.now()
        if times[2].date() == times[3].date():
            process = times[3] - times[2]
            process = process.total_seconds() / 3600
        else:
            shift_end = times[2].replace(hour=15, minute=30)
            d1 = shift_end - times[2]
            shift_start = times[3].replace(hour=7, minute=0)
            d_last = times[3] - shift_start
            delta = times[3] - times[0]
            duration3 = timedelta(hours=0)
            i_date = times[2] + timedelta(hours=24)
            cancel = False
            while cancel == False:
                if i_date.date() == times[3].date():
                    cancel = True
                else:
                    if datetime.isoweekday(i_date.date()) < 6:
                        duration3 = duration2 + timedelta(hours=8)
                i_date = i_date + timedelta(hours=24)
            process = d1 + duration3 + d_last
            process = process.total_seconds() / 3600

        return new, sent, process
