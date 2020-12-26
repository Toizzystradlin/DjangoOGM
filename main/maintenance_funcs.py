from .models import Queries, Equipment, Employees, Comment, Maintenance, Worktime, Eq_stoptime, Unstated_works
from datetime import datetime, timedelta, timezone
import pytz
import json
from django.db import connection
from . import send_message
import xlwt
from django.http import HttpResponse
from django.db.models import Q
import time
from django.shortcuts import render, redirect

months = {
    1: 'Январь',
    2: 'Февраль',
    3: 'Март',
    4: 'Апрель',
    5: 'Май',
    6: 'Июнь',
    7: 'Июль',
    8: 'Август',
    9: 'Сентябрь',
    10: 'Октябрь',
    11: 'Ноябрь',
    12: 'Декабрь'
}

def move_to(request, to_id):
    new_date = request.POST.get('date')
    reason = request.POST.get('reason')
    to = Maintenance.objects.get(id=to_id)
    to.plan2_date = new_date
    to.status = 'Перенесено'
    to.status2 = 'Перенесено с ' + months[to.plan_date.month]
    to.reason = reason
    to.save()
    return redirect('/main/maintenance' + str(to_id))

def change_time(request, to_id):
    start_time = request.POST.get('start_datetime')
    end_time = request.POST.get('end_datetime')
    to = Maintenance.objects.get(id=to_id)
    to.start_time = start_time
    to.end_time = end_time
    to.save()
    return redirect('/main/maintenance/' + str(to_id))