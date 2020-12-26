from django.shortcuts import render, redirect
from .models import Queries, Equipment, Employees, Comment, Maintenance, Worktime, Eq_stoptime, Reasons, Type, Dates, Supplies, Unstated_works, Daily_tasks
from . import send_message, funcs

def reappoint_work(request, work_id):
    doers = request.POST.getlist('emp_select')
    work = Unstated_works.objects.get(work_id=work_id)
    funcs.appoint_doers_work(doers, work.work_id)
    return redirect('main/works')

def reappoint_query(request, query_id):
    doers = request.POST.getlist('emp_select')
    query = Queries.objects.get(query_id=query_id)
    funcs.appoint_doers(doers, query.query_id)
    return redirect('main')

def reappoint_to(request, to_id):
    doers = request.POST.getlist('emp_select')
    #to = Maintenance.objects.get(id=to_id)
    funcs.appoint_doers_to(doers, to_id)
    return redirect('/main/maintenance')