from django.shortcuts import render, redirect
from .models import Queries, Equipment, Employees, Comment, Maintenance, Worktime, Eq_stoptime, Reasons, Type, Dates, Supplies, Unstated_works, Daily_tasks
from django.http import Http404, HttpResponse
from django.views.generic import ListView, DetailView
from django.db import connection
from datetime import datetime, timedelta, timezone
from OGM import settings
from django.utils.timezone import now, pytz
from . import send_message, funcs
from . import qr_code
from django.contrib.auth.decorators import login_required
import json
import openpyxl
import easygui
import xlwt
from django.http import HttpResponse
import pytz
from django.core.files.storage import FileSystemStorage


@login_required
def main(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT queries.query_id, queries.post_time, equipment.eq_name, queries.reason, queries.msg, "
                       "equipment.eq_status, queries.query_status FROM queries JOIN equipment ON (queries.eq_id = "
                       "equipment.eq_id)")
        a = cursor.fetchall()
        a = list(a)
        a.reverse()
        return render(request, 'main/main.html', {'dict': a})

def tmc(request):
    #tmc = Supplies.objects.all()
    with connection.cursor() as cursor:
        cursor.execute('SELECT supplies.supply, queries.msg, equipment.eq_name, queries.query_id, queries.post_time '
                       'FROM supplies '
                       'JOIN queries ON (queries.query_id = supplies.query_id)'
                       'JOIN equipment ON (equipment.eq_id = supplies.eq_id)'
                       'WHERE LENGTH(supplies.supply) > 2')
        tmc = cursor.fetchall()
        tmc = list(tmc)
        tmc.reverse()
        cursor.execute('SELECT supplies.supply, unstated_works.what, unstated_works.work_id, unstated_works.post_time '
                       'FROM supplies '
                       'JOIN unstated_works ON (unstated_works.work_id = supplies.work_id)'
                       'WHERE LENGTH(supplies.supply) > 2')
        tmc_work = cursor.fetchall()
        tmc_work = list(tmc_work)
        tmc_work.reverse()
        cursor.execute('SELECT supplies.supply, equipment.eq_name, maintenance.comment, maintenance.end_time '
                       'FROM supplies '
                       'JOIN maintenance ON (maintenance.id = supplies.to_id)'
                       'JOIN equipment ON (equipment.eq_id = supplies.eq_id)')
        tmc_to = cursor.fetchall()
        tmc_to = list(tmc_to)
        tmc_to.reverse()
    return render(request, 'main/tmc.html', {'tmc': tmc, 'tmc_work': tmc_work, 'tmc_to': tmc_to})

@login_required
def new_query(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT eq_name FROM equipment")
        a = cursor.fetchall()
        a = list(a)

        cursor.execute("SELECT employee_id, fio FROM employees")
        emps = cursor.fetchall()
        emps = list(emps)

        area1 = list(Equipment.objects.filter(area='Механической обработки'))
        area2 = list(Equipment.objects.filter(area='Слесарный'))
        area3 = list(Equipment.objects.filter(area='Сварочный'))
        area4 = list(Equipment.objects.filter(area='Крупноузловой сборки'))
        area5 = list(Equipment.objects.filter(area='Малярный'))

        reasons = Reasons.objects.all()

    if request.method == "POST":
        a1 = request.POST.get('area1')
        a2 = request.POST.get('area2')
        a3 = request.POST.get('area3')
        a4 = request.POST.get('area4')
        a5 = request.POST.get('area5')
        new_reason = request.POST.get('reason_select')
        new_status = request.POST.get('query_status_select')
        doers = request.POST.getlist('employee_select')
        new_msg = request.POST.get('query_message')
        new_post_time = datetime.now()

        try:
            eq = Equipment.objects.get(eq_id=a1)
        except:
            pass
        try:
            eq = Equipment.objects.get(eq_id=a2)
        except:
            pass
        try:
            eq = Equipment.objects.get(eq_id=a3)
        except:
            pass
        try:
            eq = Equipment.objects.get(eq_id=a4)
        except:
            pass
        try:
            eq = Equipment.objects.get(eq_id=a5)
        except:
            pass
        try:
            eq_id = eq.eq_id
            Queries.objects.create(eq_id=eq.eq_id, reason=new_reason, query_status=new_status,
                                   msg=new_msg, post_time=new_post_time)
            eq_status = request.POST.get('eq_status_select')
            eq = Equipment.objects.get(eq_id=eq_id)
            eq.eq_status = eq_status
            eq.save()

            if eq_status == 'Остановлено':  # Блок занесения простоев в таблицу простоев
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM eq_stoptime WHERE (eq_id = %s) AND (start_time IS NULL) ORDER BY id DESC LIMIT 1",
                        [eq.eq_id])
                    result = cursor.fetchall()
                    result = list(result)
                    if len(result) == 0:
                        Eq_stoptime.objects.create(eq_id=eq.eq_id, stop_time=datetime.now())
            elif eq_status == 'Работает':
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM eq_stoptime WHERE (eq_id = %s) AND (start_time IS NULL) ORDER BY id DESC LIMIT 1",
                        [eq.eq_id])
                    result = cursor.fetchone()
                    try:
                        result = list(result)
                        if len(result) > 0:
                            i = result[0]
                            a = Eq_stoptime.objects.get(id=i)
                            a.start_time = datetime.now()
                            a.save()
                    except:
                        pass

            query = Queries.objects.all().order_by("-query_id")[0]
            funcs.appoint_doers(doers, query.query_id)
            funcs.multiple_doers(doers, query.query_id)
            return redirect('main')
        except Exception as ex:
            return HttpResponse(ex)

    else:
        pass
    return render(request, 'main/new_query.html',
                  {'name': a, 'emps': emps, 'area1': area1, 'area2': area2, 'area3': area3, 'area4': area4, 'area5': area5, 'reasons': reasons})


@login_required
def show_query(request, query_id):
    c = Queries.objects.get(query_id=query_id)
    d = Equipment.objects.get(eq_id=c.eq_id)
    reasons = Reasons.objects.all()
    now_emp = 0
    try:
        json_now_emps = c.json_emp
        now_emps_dict = json.loads(json_now_emps)
        now_emps_list = now_emps_dict['doers']
        final_emps = []
        result_now_emps = [int(item) for item in now_emps_list]  # Преобразование "1" в 1
        now_emps = []
        for i in result_now_emps:
            e = Employees.objects.get(employee_id=i)
            now_emps.append(e)
    except:
        result_now_emps = []
        final_emps = []

    emps = Employees.objects.all()
    for i in emps:  # цикл подготовки массива исполнителей для корректного вывода в селект мултипл
        m = [i.employee_id, i.fio, False]
        final_emps.append(m)
        if len(result_now_emps) > 0:
            for j in result_now_emps:
                if i.employee_id == j:
                    final_emps[-1][2] = True

    with connection.cursor() as cursor:
        cursor.execute("SELECT comments.query, comments.author, comments.text, comments.created_date, "
                       "employees.fio FROM comments JOIN employees ON (comments.query = %s) AND (comments.author = employees.employee_id)",
                       [query_id])
        coms = cursor.fetchall()
        coms = list(coms)

    with connection.cursor() as cursor:
        cursor.execute("SELECT employees.fio, supplies.supply FROM supplies JOIN employees ON (supplies.emp_id = employees.employee_id) AND (supplies.query_id = %s) WHERE LENGTH(supplies.supply) > 2",
                       [query_id])
        supplies = cursor.fetchall()
        supplies = list(supplies)

    with connection.cursor() as cursor:
        cursor.execute("SELECT worktime.query_id, worktime.start_time, worktime.stop_time, employees.fio FROM "
                       "worktime JOIN employees ON (worktime.employee_id = employees.employee_id) AND (worktime.query_id = %s)",
                       [query_id])
        works = cursor.fetchall()
        works = list(works)

    return render(request, 'main/query.html',
                  {'query': c, 'equipment': d, 'coms': coms, 'supplies': supplies, 'works': works, 'emps': emps, 'now_emp': now_emp,
                   'final_emps': final_emps, 'reasons': reasons})


@login_required
def edit_query(request, query_id):
    if request.method == "POST":

        q_status = request.POST.get('query_status_select')
        q_reason = request.POST.get('query_reason_select')
        eq_status = request.POST.get('eq_status_select')
        q_comment = request.POST.get('comment')
        doers = request.POST.getlist('emp_select')

        q = Queries.objects.get(query_id=query_id)
        e = Equipment.objects.get(eq_id=q.eq_id)

        q.query_status = q_status
        q.comment = q_comment
        q.reason = q_reason
        q.save()
        funcs.appoint_doers_2(doers, query_id)  # занести json файл
        funcs.multiple_doers(doers, query_id)
        e.eq_status = eq_status
        e.save()

        if eq_status == 'Остановлено':  # Блок занесения простоев в таблицу простоев
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM eq_stoptime WHERE (eq_id = %s) AND (start_time IS NULL) ORDER BY id DESC LIMIT 1",
                    [q.eq_id])
                result = cursor.fetchall()
                result = list(result)
                if len(result) == 0:
                    Eq_stoptime.objects.create(eq_id=q.eq_id, stop_time=datetime.now())
        elif eq_status == 'Работает':
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM eq_stoptime WHERE (eq_id = %s) AND (start_time IS NULL) ORDER BY id DESC LIMIT 1",
                    [q.eq_id])
                result = cursor.fetchone()
                try:
                    result = list(result)
                    if len(result) > 0:
                        i = result[0]
                        a = Eq_stoptime.objects.get(id=i)
                        a.start_time = datetime.now()
                        a.save()
                except:
                    pass

        if q_status == 'Завершена':
            with connection.cursor() as cursor:
                cursor.execute('UPDATE worktime SET stop_time = %s WHERE query_id = %s', [datetime.now(), query_id])
                cursor.execute('UPDATE queries SET stop_time = %s WHERE query_id = %s', [datetime.now(), query_id])

    return redirect('main')

def works(request):
    works = Unstated_works.objects.all()
    with connection.cursor() as cursor:
        cursor.execute('SELECT unstated_works.work_id, unstated_works.what, unstated_works.post_time, '
                       'unstated_works.query_status FROM unstated_works')
        xworks = list(cursor.fetchall())
    return render(request, 'main/works.html', {'works': works, 'xworks': xworks})

def show_work(request, work_id):
    c = Unstated_works.objects.get(work_id=work_id)
    now_emp = 0
    try:
        json_now_emps = c.json_emp
        now_emps_dict = json.loads(json_now_emps)
        now_emps_list = now_emps_dict['doers']
        final_emps = []
        result_now_emps = [int(item) for item in now_emps_list]  # Преобразование "1" в 1
        now_emps = []
        for i in result_now_emps:
            e = Employees.objects.get(employee_id=i)
            now_emps.append(e)
    except:
        result_now_emps = []
        final_emps = []

    emps = Employees.objects.all()
    for i in emps:  # цикл подготовки массива исполнителей для корректного вывода в селект мултипл
        m = [i.employee_id, i.fio, False]
        final_emps.append(m)
        if len(result_now_emps) > 0:
            for j in result_now_emps:
                if i.employee_id == j:
                    final_emps[-1][2] = True

    with connection.cursor() as cursor:
        cursor.execute("SELECT comments.query, comments.author, comments.text, comments.created_date, "
                       "employees.fio FROM comments JOIN employees ON (comments.work = %s) AND (comments.author = employees.employee_id)",
                       [work_id])
        coms = cursor.fetchall()
        coms = list(coms)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT employees.fio, supplies.supply FROM supplies JOIN employees ON (supplies.emp_id = employees.employee_id) AND (supplies.work_id = %s) WHERE LENGTH(supplies.supply) > 2",
            [work_id])
        supplies = cursor.fetchall()
        supplies = list(supplies)

    with connection.cursor() as cursor:
        cursor.execute("SELECT worktime.work_id, worktime.start_time, worktime.stop_time, employees.fio FROM "
                       "worktime JOIN employees ON (worktime.employee_id = employees.employee_id) AND (worktime.work_id = %s)",
                       [work_id])
        works = cursor.fetchall()
        works = list(works)

    return render(request, 'main/work.html',
                  {'work': c, 'coms': coms, 'supplies': supplies, 'works': works, 'emps': emps,
                   'now_emp': now_emp,
                   'final_emps': final_emps})

def edit_work(request, work_id):
    if request.method == 'POST':
        work_status = request.POST.get('work_status_select')
        x = Unstated_works.objects.get(work_id=work_id)
        x.query_status = work_status
        x.save()
        return redirect('works')

def new_work(request):
    if request.method == 'POST':
        text = request.POST.get('work_message')
        doers = request.POST.getlist('work_employee_select')
        Unstated_works.objects.create(what=text, post_time= datetime.now(), query_status='Новая')
        work = Unstated_works.objects.all().order_by("-work_id")[0]
        funcs.appoint_doers_work(doers, work.work_id)

    return redirect('works')

def reappoint_work(request, work_id):
    doers = request.POST.getlist('emp_select')
    work = Unstated_works.objects.get(work_id=work_id)
    funcs.appoint_doers_work(doers, work.work_id)
    return redirect('works')


def delete_work(request, work_id):
    x = Unstated_works.objects.get(work_id=work_id)
    x.delete()
    return redirect('/main/works')

@login_required
def show_equipment(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM equipment")
        eqs = cursor.fetchall()
        eqs = list(eqs)

    return render(request, 'main/equipment.html', {'eqs': eqs})


@login_required
def show_eq(request, eq_id):
    eqs = Equipment.objects.get(eq_id=eq_id)
    with connection.cursor() as cursor:
        cursor.execute("SELECT queries.query_id, queries.post_time, queries.reason, queries.msg, "
                       "queries.query_status FROM queries WHERE (queries.eq_id = %s)", [eq_id])
        qs = cursor.fetchall()
        qs = list(qs)
        qs.reverse()

        cursor.execute("SELECT id, start_time, comment, status FROM maintenance WHERE (eq_id = %s)", [eq_id])
        tos = list(cursor.fetchall())

        cursor.execute("SELECT supply, query_id FROM supplies WHERE (eq_id = %s)", [eq_id])
        supplies = list(cursor.fetchall())

    equipment = Equipment.objects.filter(eq_id=eq_id)
    name, mean, shifts, invs = funcs.top10(equipment)
    name_m, mean_m, shifts_m, invs_m = funcs.top10_month(equipment)

    last_week_name, last_week_mean, sh, invnums = funcs.top10_last_week(equipment)

    return render(request, 'main/eq_one.html',
                  {'eqs': eqs, 'queries': qs, 'name': name, 'mean': str(mean[0])[:5], 'mean_m': str(mean_m[0])[:5],
                   'tos': tos, 'last_week_name': last_week_name, 'last_week_mean': str(last_week_mean[0])[:5],
                   'invnums': invnums, 'supplies': supplies})


@login_required
def edit_eq(request, eq_id):
    if request.method == 'POST':
        eqs = Equipment.objects.get(eq_id=eq_id)
        eq_status = request.POST.get('eq_status_select')
        eq_category = request.POST.get('category_select')
        eqs.category = eq_category
        eqs.eq_status = eq_status
        eqs.shift = request.POST.get('shift_select')
        eqs.save()
        eqs.eq_comment = request.POST.get('eq_comment')
        eqs.save()


        if eq_status == 'Остановлено':  # Блок занесения простоев в таблицу простоев
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM eq_stoptime WHERE (eq_id = %s) AND (start_time IS NULL) ORDER BY id DESC LIMIT 1",
                    [eq_id])
                result = cursor.fetchall()
                result = list(result)
                if len(result) == 0:
                    Eq_stoptime.objects.create(eq_id=eq_id, stop_time=datetime.now())
        elif eq_status == 'Работает':
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM eq_stoptime WHERE (eq_id = %s) AND (start_time IS NULL) ORDER BY id DESC LIMIT 1",
                    [eq_id])
                result = cursor.fetchone()
                try:
                    result = list(result)
                    if len(result) > 0:
                        i = result[0]
                        a = Eq_stoptime.objects.get(id=i)
                        a.start_time = datetime.now()
                        a.save()
                except:
                    pass

    return redirect('/main/equipment')


@login_required
def new_eq(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM types")
        tps = cursor.fetchall()
        tps = list(tps)

    if request.method == "POST":
        new_name = request.POST.get('new_name')
        new_num = request.POST.get('new_num')
        new_type = request.POST.get('type_select')
        new_area = request.POST.get('area_select')
        shift = request.POST.get('shift_select')

        Equipment.objects.create(eq_name=new_name, invnum=new_num, eq_type=new_type, area=new_area, shift=shift)
        max_eq = Equipment.objects.all().order_by('-eq_id')[0]
        max_id = max_eq.eq_id
        qr_code.create_qr(max_id)

        return redirect('/main/equipment')
    return render(request, 'main/new_eq.html', {'types': tps})

def upload_photo_eq(request, eq_id):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        fs.delete(str(eq_id) + '.jpg')
        filename = fs.save(str(eq_id) + '.jpg', myfile)
        #uploaded_file_url = fs.url(filename)
        eqs = Equipment.objects.get(eq_id=eq_id)
        with connection.cursor() as cursor:
            cursor.execute("SELECT queries.query_id, queries.post_time, queries.reason, queries.msg, "
                           "queries.query_status FROM queries WHERE (queries.eq_id = %s)", [eq_id])
            qs = cursor.fetchall()
            qs = list(qs)
            qs.reverse()

            cursor.execute("SELECT id, start_time, comment, status FROM maintenance WHERE (eq_id = %s)", [eq_id])
            tos = list(cursor.fetchall())

            cursor.execute("SELECT supply, query_id FROM supplies WHERE (eq_id = %s)", [eq_id])
            supplies = list(cursor.fetchall())

        equipment = Equipment.objects.filter(eq_id=eq_id)
        name, mean, shifts, invs = funcs.top10(equipment)
        name_m, mean_m, shifts_m, invs_m = funcs.top10_month(equipment)

        last_week_name, last_week_mean, sh, invnums = funcs.top10_last_week(equipment)

        return render(request, 'main/eq_one.html',
                      {'eqs': eqs, 'queries': qs, 'name': name, 'mean': str(mean[0])[:5], 'mean_m': str(mean_m[0])[:5],
                       'tos': tos, 'last_week_name': last_week_name, 'last_week_mean': str(last_week_mean[0])[:5],
                       'invnums': invnums, 'supplies': supplies})

@login_required
def show_employees(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM employees")
        emps = cursor.fetchall()
        emps = list(emps)

    return render(request, 'main/employees.html', {'emps': emps})


@login_required
def show_emp(request, employee_id):
    emp = Employees.objects.get(employee_id=employee_id)
    man_id = emp.employee_id
    with connection.cursor() as cursor:
        cursor.execute("SELECT equipment.eq_name, queries.post_time, " \
                       "queries.msg, queries.query_status, queries.query_id, queries.json_emp FROM " \
                       "queries JOIN equipment ON ((queries.eq_id = equipment.eq_id) AND (" \
                       "queries.query_status != 'Завершена')) ")
        all_queries = cursor.fetchall()
        my_queries = []
        for i in all_queries:  # сортировка по значению json файла
            json_emps_dict = json.loads(i[5])
            json_emps_list = json_emps_dict['doers']
            result_emps_list = [int(item) for item in json_emps_list]
            for j in result_emps_list:
                if j == man_id:
                    my_queries.append(i)

        cursor.execute("SELECT equipment.eq_name, queries.post_time, " \
                       "queries.msg, queries.query_status, queries.query_id, queries.json_emp FROM " \
                       "equipment JOIN queries ON ((queries.eq_id = equipment.eq_id) AND (" \
                       "queries.query_status = 'Завершена')) ")
        all_queries = cursor.fetchall()
        my_queries_done = []
        for i in all_queries:  # сортировка по значению json файла
            json_emps_dict = json.loads(i[5])
            json_emps_list = json_emps_dict['doers']
            result_emps_list = [int(item) for item in json_emps_list]
            for j in result_emps_list:
                if j == man_id:
                    my_queries_done.append(i)

        cursor.execute(
            "SELECT maintenance.start_time, maintenance.employee_id, maintenance.end_time, maintenance.status, " \
            "equipment.eq_name, maintenance.id FROM maintenance JOIN equipment ON (maintenance.eq_id = equipment.eq_id)")
        all_tos = cursor.fetchall()
        my_tos = []
        for i in all_tos:
            json_emps_dict = json.loads(i[1])
            json_emps_list = json_emps_dict['doers']
            result_emps_list = [int(item) for item in json_emps_list]
            for j in result_emps_list:
                if j == man_id:
                    my_tos.append(i)

    return render(request, 'main/edit_emp.html',
                  {'emp': emp, 'queries': my_queries, 'done_queries': my_queries_done, 'my_tos': my_tos})


@login_required
def add_new(request):
    return render(request, 'main/add_new.html')


@login_required
def save_emp(request):
    name = request.POST.get('new_name')
    rank = request.POST.get('rank')
    tg_id = request.POST.get('tg_id')
    master = request.POST.get('master_check')

    Employees.objects.create(fio=name, rank=rank, tg_id=tg_id, master=master)
    return redirect('/main/employees')


@login_required
def stats(request):
    go_count = Queries.objects.filter(query_status='В процессе').count()
    new_count = Queries.objects.filter(query_status='Новая').count()
    postpone_count = Queries.objects.filter(query_status='отложена').count()
    got_count = Queries.objects.filter(query_status='Принята').count()

    work_count = Equipment.objects.filter(eq_status='Работает').count()
    stop_count = Equipment.objects.filter(eq_status='Остановлено').count()
    to_count = Equipment.objects.filter(eq_status='ТО').count()

    equipment = Equipment.objects.all()  # топ 10 по простою за все время
    names, means, sh, invs_all = funcs.top10(equipment)  # возвращает имена, цифры по простою и смены оборудования
    equipment = Equipment.objects.all()  # топ 10 по простою за month
    names_m, means_m, sh_m, invs_month = funcs.top10_month(equipment)
    names_week, means_week, shifts_week, invnums = funcs.top10_last_week(equipment)# топ 10 по простою за week

    equipment = Equipment.objects.filter(area='Механической обработки')
    names_mech, means_mech, shifts_mech, invs_mech = funcs.top10(equipment)
    equipment = Equipment.objects.filter(area='Механической обработки')
    names_mech_month, means_mech_month, shifts_mech_month, invs_mech_month = funcs.top10_month(equipment)

    equipment = Equipment.objects.filter(area='Слесарный')
    names_smith, means_smith, shifts_smith, invs_smith = funcs.top10(equipment)
    equipment = Equipment.objects.filter(area='Слесарный')
    names_smith_month, means_smith_month, shifts_smith_month, invs_smith_month = funcs.top10_month(equipment)

    equipment = Equipment.objects.filter(area='Сварочный')
    names_weld, means_weld, shifts_weld, invs_weld = funcs.top10(equipment)
    equipment = Equipment.objects.filter(area='Сварочный')
    names_weld_month, means_weld_month, shifts_weld_month, invs_weld_month = funcs.top10_month(equipment)

    try:
        to = list(Maintenance.objects.filter(status='Завершено'))
        to[:20]
        to_names = []
        for i in to:
            item = Equipment.objects.get(eq_id=i.eq_id)
            x = item.eq_name
            to_names.append(x)
        average_time = timedelta()
        to_times = []
        for i in to:
            delta = i.end_time - i.start_time
            time = delta.total_seconds() / 3600
            to_times.append(time)
            average_time = average_time + delta
        average_time = average_time / len(to)
    except:
        return render(request, 'main/stats.html', {'go_count': go_count, 'new_count': new_count,
                                                   'postpone_count': postpone_count,
                                                   'got_count': got_count, 'work_count': work_count,
                                                   'stop_count': stop_count,
                                                   'to_count': to_count, 'names': names, 'means': means, 'shifts': sh, 'invs_all': invs_all,
                                                   'names_week': names_week, 'means_week': means_week,
                                                   'shifts_week': shifts_week, 'invnums': invnums,
                                                   'names_m': names_m, 'means_m': means_m, 'shifts_m': sh_m, 'invs_month': invs_month,
                                                   'names_mech': names_mech,
                                                   'means_mech': means_mech, 'shifts_mech': shifts_mech, 'invs_mech': invs_mech,
                                                   'names_mech_month': names_mech_month,
                                                   'means_mech_month': means_mech_month,
                                                   'shifts_mech_month': shifts_mech_month, 'invs_mech_month': invs_mech_month,
                                                   'names_smith': names_smith, 'means_smith': means_smith,
                                                   'shifts_smith': shifts_smith, 'invs_smith': invs_smith,
                                                   'names_smith_month': names_smith_month,
                                                   'means_smith_month': means_smith_month,
                                                   'shifts_smith_month': shifts_smith_month, 'invs_smith_month': invs_smith_month,
                                                   'names_weld': names_weld, 'means_weld': means_weld,
                                                   'shifts_weld': shifts_weld, 'invs_weld': invs_weld,
                                                   'names_weld_month': names_weld_month,
                                                   'means_weld_month': means_weld_month,
                                                   'shifts_weld_month': shifts_weld_month, 'invs_weld_month': invs_weld_month
                                                   })

    return render(request, 'main/stats.html', {'go_count': go_count, 'new_count': new_count,
                                                   'postpone_count': postpone_count,
                                                   'got_count': got_count, 'work_count': work_count,
                                                   'stop_count': stop_count,
                                                   'to_count': to_count, 'names': names, 'means': means, 'shifts': sh, 'invs_all': invs_all,
                                                   'names_week': names_week, 'means_week': means_week,
                                                   'shifts_week': shifts_week, 'invnums': invnums,
                                                   'names_m': names_m, 'means_m': means_m, 'shifts_m': sh_m, 'invs_month': invs_month,
                                                   'names_mech': names_mech,
                                                   'means_mech': means_mech, 'shifts_mech': shifts_mech, 'invs_mech': invs_mech,
                                                   'names_mech_month': names_mech_month,
                                                   'means_mech_month': means_mech_month,
                                                   'shifts_mech_month': shifts_mech_month, 'invs_mech_month': invs_mech_month,
                                                   'names_smith': names_smith, 'means_smith': means_smith,
                                                   'shifts_smith': shifts_smith, 'invs_smith': invs_smith,
                                                   'names_smith_month': names_smith_month,
                                                   'means_smith_month': means_smith_month,
                                                   'shifts_smith_month': shifts_smith_month, 'invs_smith_month': invs_smith_month,
                                                   'names_weld': names_weld, 'means_weld': means_weld,
                                                   'shifts_weld': shifts_weld, 'invs_weld': invs_weld,
                                                   'names_weld_month': names_weld_month,
                                                   'means_weld_month': means_weld_month,
                                                   'shifts_weld_month': shifts_weld_month, 'invs_weld_month': invs_weld_month
                                                   })

def stats2(request):
    equipment = Equipment.objects.all()
    area_title = 'Все участки'
    utc = pytz.UTC
    today = datetime.today()
    weekday = today.weekday()
    start_delta = timedelta(days=weekday, weeks=1)
    last_week_start = today - start_delta
    last_week_end = last_week_start + timedelta(days=6)
    s1 = [int(last_week_start.year), int(last_week_start.month), int(last_week_start.day)]
    s2 = [int(last_week_end.year), int(last_week_end.month), int(last_week_end.day)]

    go_count = Queries.objects.filter(query_status='В процессе').count()
    new_count = Queries.objects.filter(query_status='Новая').count()
    postpone_count = Queries.objects.filter(query_status='отложена').count()
    got_count = Queries.objects.filter(query_status='Принята').count()

    work_count = Equipment.objects.filter(eq_status='Работает').count()
    stop_count = Equipment.objects.filter(eq_status='Остановлено').count()
    to_count = Equipment.objects.filter(eq_status='ТО').count()

    to_times = funcs.to('Все участки', s1, s2)
    queries_ids, to_ids, queries_count, tos_count = funcs.period_queries_and_to('Все участки', s1, s2)
    names_period, means_period, means_to_period, invs_period, full_plain, full_plain_to = funcs.plain_period(equipment, s1, s2)

    equipment = Equipment.objects.filter(category='A')
    plain_list, maintenance_list, expected_time_list, usefull_hours, kpi_list, dates, kpi_pairs_a = funcs.time_kpi(equipment, s1, s2)
    equipment = Equipment.objects.filter(category='B')
    plain_list_b, maintenance_list_b, expected_time_list_b, usefull_hours_b, kpi_list_b, dates_b, kpi_pairs_b = funcs.time_kpi(equipment, s1, s2)

    if request.method == 'POST':
        try:
            a = Dates.objects.get(chart='kpi_a')
            a.kpi_a_start = request.POST.get('kpi_a_start')
            a.kpi_a_end = request.POST.get('kpi_a_end')
            a.save()
            a = Dates.objects.get(chart='kpi_a')
            year_start = int(str(a.kpi_a_start.year))
            month_start = int(str(a.kpi_a_start.month))
            day_start = int(str(a.kpi_a_start.day))
            s1 = [year_start, month_start, day_start]
            year_end = int(str(a.kpi_a_end.year))
            month_end = int(str(a.kpi_a_end.month))
            day_end = int(str(a.kpi_a_end.day))
            s2 = [year_end, month_end, day_end]
            s3 = request.POST.get('step')
            equipment = Equipment.objects.filter(category='A')
            plain_list, maintenance_list, expected_time_list, usefull_hours, kpi_list, dates, kpi_pairs_a = funcs.time_kpi(
                equipment, s1, s2, s3)
            equipment = Equipment.objects.filter(category='B')
            plain_list_b, maintenance_list_b, expected_time_list_b, usefull_hours_b, kpi_list_b, dates_b, kpi_pairs_b = funcs.time_kpi(
                equipment, s1, s2, s3)
            area = request.POST.get('area')
            equipment = Equipment.objects.filter(area=area)
            if area == 'Все участки':
                equipment = Equipment.objects.all()
            area_title = area
            names_period, means_period, means_to_period, invs_period, full_plain, full_plain_to = funcs.plain_period(equipment, s1, s2)
            queries_ids, to_ids, queries_count, tos_count = funcs.period_queries_and_to(area, s1, s2)
            to_times = funcs.to(area, s1, s2)
        except: pass
    queries = []
    tos = []
    with connection.cursor() as cursor:
        for i in queries_ids:
            cursor.execute(
                "SELECT queries.query_id, queries.post_time, queries.stop_time, equipment.eq_name, equipment.eq_status, "
                "queries.msg, queries.query_status FROM queries JOIN equipment ON (queries.eq_id = equipment.eq_id) AND (queries.query_id = %s)",
                [i])
            queries.append(cursor.fetchone())
        for i in to_ids:
            cursor.execute("SELECT maintenance.id, maintenance.start_time, maintenance.end_time, equipment.eq_name, "
                           "equipment.eq_status, maintenance.comment, maintenance.status FROM maintenance JOIN "
                           "equipment ON (maintenance.eq_id = equipment.eq_id) AND (maintenance.id = %s)", [i])
            tos.append(cursor.fetchone())

    return render(request, 'main/stats2.html', {'queries_ids': queries_ids, 'to_ids': to_ids, 'queries': queries, 'tos': tos,
                                                'queries_count': queries_count, 'tos_count': tos_count,
                                                'to_times': to_times,
                                                'plain_list': plain_list, 'maintenance_list': maintenance_list, 'expected_time_list': expected_time_list, 'usefull_hours': usefull_hours, 'kpi_list': kpi_list, 'dates': dates,
                                                'kpi_list_b': kpi_list_b, 'dates_b': dates_b,
                                                'names_period': names_period, 'means_period': means_period, 'means_to_period': means_to_period, 'invs_period': invs_period,
                                                'start': s1, 'end': s2,
                                                'full_plain': full_plain, 'full_plain_to': full_plain_to,
                                                'area_title': area_title,
                                                'go_count': go_count, 'new_count': new_count,
                                                'postpone_count': postpone_count,
                                                'got_count': got_count, 'work_count': work_count,
                                                'stop_count': stop_count,
                                                'to_count': to_count
                                                })

@login_required
def export__data(request):
    equipment = Equipment.objects.all()  # топ 10 по простою за все время
    names, means, sh = funcs.top10(equipment)  # возвращает имена, цифры по простою и смены оборудования
    equipment = Equipment.objects.all()  # топ 10 по простою за месяц
    names_m, means_m, sh_m = funcs.top10_month(equipment)

    equipment = Equipment.objects.filter(area='Механической обработки')
    names_mech, means_mech, shifts_mech = funcs.top10(equipment)
    equipment = Equipment.objects.filter(area='Механической обработки')
    names_mech_month, means_mech_month, shifts_mech_month = funcs.top10_month(equipment)

    equipment = Equipment.objects.filter(area='Слесарный')
    names_smith, means_smith, shifts_smith = funcs.top10_month(equipment)
    equipment = Equipment.objects.filter(area='Слесарный')
    names_smith_month, means_smith_month, shifts_smith_month = funcs.top10_month(equipment)

    equipment = Equipment.objects.filter(area='Сварочный')
    names_weld, means_weld, shifts_weld = funcs.top10_month(equipment)
    equipment = Equipment.objects.filter(area='Сварочный')
    names_weld_month, means_weld_month, shifts_weld_month = funcs.top10_month(equipment)

    to = list(Maintenance.objects.filter(status='Завершено'))
    to[:20]
    to_names = []
    for i in to:
        item = Equipment.objects.get(eq_id=i.eq_id)
        x = item.eq_name
        to_names.append(x)
    average_time = timedelta()
    to_times = []
    for i in to:
        delta = i.end_time - i.start_time
        time = delta.total_seconds() / 3600
        to_times.append(str(time))
        average_time = average_time + delta
    average_time = average_time / len(to)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="stats.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('stats')  # this will make a sheet named Users Data

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    def write_data(start_row, start_col, names, means):
        row = start_row
        col = start_col
        for i in names:
            ws.write(row, col, i, font_style)
            row = row + 1
        row = start_row
        col = start_col + 1
        for i in means:
            ws.write(row, col, i, font_style)
            row = row + 1

    ws.write(0, 0, 'Топ 10 по простою', font_style)
    ws.write(0, 3, 'Топ 10 по простою мех. обработка', font_style)
    ws.write(0, 6, 'Топ 10 по простою сварка', font_style)
    ws.write(0, 9, 'Топ 10 по простою слесарный', font_style)
    write_data(1, 0, names, means)
    write_data(1, 3, names_mech, means_mech)
    write_data(1, 6, names_weld, means_weld)
    write_data(1, 9, names_smith, means_smith)

    ws.write(15, 0, 'Топ 10 по простою за месяц', font_style)
    ws.write(15, 3, 'Топ 10 по простою мех. обработка за месяц', font_style)
    ws.write(15, 6, 'Топ 10 по простою сварка за месяц', font_style)
    ws.write(15, 9, 'Топ 10 по простою слесарный за месяц', font_style)
    write_data(16, 0, names_m, means_m)
    write_data(16, 3, names_mech_month, means_mech_month)
    write_data(16, 6, names_weld_month, means_weld_month)
    write_data(16, 9, names_smith_month, means_smith_month)

    ws.write(30, 0, 'Среднее время ТО', font_style)
    ws.write(31, 0, str(average_time), font_style)

    ws.write(30, 3, 'Среднее время ТО', font_style)
    write_data(31, 3, to_names, to_times)

    wb.save(response)
    return response


@login_required
def maintenance(request):
    a = list(Maintenance.objects.all())
    for i in a:
        if (i.start_time.month > i.plan_date.month) and i.end_time:
            delta = i.start_time - i.plan_date
            i.status2 = 'Выполнено с опозданием ' + str(delta.days) + ' дней'
            i.save()
        elif i.status == 'Новое':
            if i.plan_date.month < datetime.now().month:
                delta = datetime.now().date() - i.plan_date.date()
                i.status2 = 'Просрочено на ' + str(delta.days) + ' дней'
                i.save()
            else:
                i.status2 = 'Новое'
                i.save()
        elif (i.start_time.month < i.plan_date.month) and i.end_time:
            delta = i.start_time - i.plan_date
            i.status2 = 'Выполнено раньше на ' + str(abs(delta.days)) + ' дней'
            i.save()
        elif (i.start_time.month == i.plan_date.month) and i.end_time:
            i.status2 = 'Выполнено в срок '
            i.save()

    with connection.cursor() as cursor:
        cursor.execute("SELECT equipment.eq_name, equipment.invnum, equipment.eq_type, equipment.area, "
                       "maintenance.start_time, maintenance.employee_id, maintenance.comment, maintenance.id, maintenance.status2 FROM equipment JOIN "
                       "maintenance ON (equipment.eq_id = maintenance.eq_id) and (end_time IS NULL) and (status = 'Новое')")
        tos = cursor.fetchall()
        tos = list(tos)
        tos.reverse()  # список с запланированными ТО

        cursor.execute("SELECT equipment.eq_name, equipment.invnum, equipment.eq_type, equipment.area, "
                       "maintenance.start_time, maintenance.end_time, maintenance.employee_id, maintenance.comment, maintenance.id, maintenance.status2 FROM equipment JOIN "
                       "maintenance ON (equipment.eq_id = maintenance.eq_id) and (end_time IS NOT NULL) and (status = 'Завершено')")

        tos2 = cursor.fetchall()
        tos2 = list(tos2)
        tos2.reverse()  # список с выполнеными ТО

        cursor.execute("SELECT equipment.eq_name, equipment.invnum, equipment.eq_type, equipment.area, "
                       "maintenance.start_time, maintenance.end_time, maintenance.employee_id, maintenance.comment, maintenance.id FROM equipment JOIN "
                       "maintenance ON (equipment.eq_id = maintenance.eq_id) and (maintenance.status = 'В процессе')")

        tos3 = cursor.fetchall()
        tos3 = list(tos3)
        tos3.reverse()  # список с в процеесе ТО

    return render(request, 'main/maintenance.html', {'tos': tos, 'tos2': tos2, 'tos3': tos3})


@login_required
def new_maintenance(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT employee_id, fio FROM employees")
        emps = cursor.fetchall()
        emps = list(emps)

        area1 = list(Equipment.objects.filter(area='Механической обработки'))
        area2 = list(Equipment.objects.filter(area='Слесарный'))
        area3 = list(Equipment.objects.filter(area='Сварочный'))
        area4 = list(Equipment.objects.filter(area="Крупноузловой сборки"))
    if request.method == 'POST':
        # eq_id = request.POST.get('eq_name_select')
        new_date = request.POST.get('date')
        # new_emp = request.POST.get('employee_select')
        comment = request.POST.get('comment')
        expected_time = request.POST.get('expected_time')

        a1 = request.POST.get('area1')
        a2 = request.POST.get('area2')
        a3 = request.POST.get('area3')
        a4 = request.POST.get('area4')
        doers = request.POST.getlist('employee_select')
        try:
            eq = Equipment.objects.get(eq_id=a1)
        except:
            pass
        try:
            eq = Equipment.objects.get(eq_id=a2)
        except:
            pass
        try:
            eq = Equipment.objects.get(eq_id=a3)
        except:
            pass
        try:
            eq = Equipment.objects.get(eq_id=a4)
        except:
            pass

        Maintenance.objects.create(comment=comment, eq_id=eq.eq_id, status='Новое', expected_time=expected_time, plan_date=new_date)

        to = Maintenance.objects.all().order_by("-id")[0]
        funcs.appoint_doers_to(doers, to.id)

        return redirect('/main/maintenance')

    return render(request, 'main/new_maintenance.html',
                  {'emps': emps, 'area1': area1, 'area2': area2, 'area3': area3, 'area4': area4})


@login_required
def show_maintenance(request, maintenance_id):
    c = Maintenance.objects.get(id=maintenance_id)
    b = Equipment.objects.get(eq_id=c.eq_id)
    now_emp = 0
    try:
        json_now_emps = c.employee_id
        now_emps_dict = json.loads(json_now_emps)
        now_emps_list = now_emps_dict['doers']
        final_emps = []
        result_now_emps = [int(item) for item in now_emps_list]  # Преобразование "1" в 1
        now_emps = []
        for i in result_now_emps:
            e = Employees.objects.get(employee_id=i)
            now_emps.append(e)
    except:
        result_now_emps = []
        final_emps = []

    emps = Employees.objects.all()
    for i in emps:  # цикл подготовки массива исполнителей для корректного вывода в селект мултипл
        m = [i.employee_id, i.fio, False]
        final_emps.append(m)
        if len(result_now_emps) > 0:
            for j in result_now_emps:
                if i.employee_id == j:
                    final_emps[-1][2] = True

    return render(request, 'main/show_maintenance.html',
                  {'eq': b, 'to': c, 'emps': emps, 'now_emp': now_emp, 'final_emps': final_emps})


@login_required
def maintenance_edit(request, to_id):
    a = Maintenance.objects.get(id=to_id)
    start_date = request.POST.get('date')
    end_date = request.POST.get('date2')
    doers = request.POST.getlist('emp_select')
    funcs.appoint_doers_to(doers, to_id)
    comment = request.POST.get('comment')
    if end_date != '':
        a.end_time = end_date
    a.start_time = start_date
    a.comment = comment
    a.save()

    return redirect('/main/maintenance')


@login_required
def pc_query(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT eq_name FROM equipment")
        a = cursor.fetchall()
        a = list(a)

        area1 = list(Equipment.objects.filter(area='Механической обработки'))
        area2 = list(Equipment.objects.filter(area='Слесарный'))
        area3 = list(Equipment.objects.filter(area='Сварочный'))
        area4 = list(Equipment.objects.filter(area='Крупноузловой сборки'))
        area5 = list(Equipment.objects.filter(area='Малярный'))
        reasons = Reasons.objects.all()
    if request.method == "POST":
        area1 = request.POST.get('area1')
        area2 = request.POST.get('area2')
        area3 = request.POST.get('area3')
        area4 = request.POST.get('area4')
        area5 = request.POST.get('area5')
        new_reason = request.POST.get('reason_select')
        new_msg = request.POST.get('query_message')
        new_post_time = datetime.now()
        doers = []
        try:
            eq = Equipment.objects.get(eq_id=area1)
        except:
            pass
        try:
            eq = Equipment.objects.get(eq_id=area2)
        except:
            pass
        try:
            eq = Equipment.objects.get(eq_id=area3)
        except:
            pass
        try:
            eq = Equipment.objects.get(eq_id=area4)
        except:
            pass
        try:
            eq = Equipment.objects.get(eq_id=area5)
        except:
            pass
        try:
            eq_id = eq.eq_id
            Queries.objects.create(eq_id=eq.eq_id, reason=new_reason, query_status='Новая',
                                   msg=new_msg, post_time=new_post_time)
            eq_status = request.POST.get('eq_status_select')
            eq = Equipment.objects.get(eq_id=eq_id)
            eq.eq_status = eq_status
            eq.save()

            if eq_status == 'Остановлено':  # Блок занесения простоев в таблицу простоев
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM eq_stoptime WHERE (eq_id = %s) AND (start_time IS NULL) ORDER BY id DESC LIMIT 1",
                        [eq.eq_id])
                    result = cursor.fetchall()
                    result = list(result)
                    if len(result) == 0:
                        Eq_stoptime.objects.create(eq_id=eq.eq_id, stop_time=datetime.now())
            elif eq_status == 'Работает':
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM eq_stoptime WHERE (eq_id = %s) AND (start_time IS NULL) ORDER BY id DESC LIMIT 1",
                        [eq.eq_id])
                    result = cursor.fetchone()
                    try:
                        result = list(result)
                        if len(result) > 0:
                            i = result[0]
                            a = Eq_stoptime.objects.get(id=i)
                            a.start_time = datetime.now()
                            a.save()
                    except:
                        pass
            query = Queries.objects.all().order_by("-query_id")[0]
            funcs.appoint_doers(doers, query.query_id)
            send_message.send_message_1(query.query_id, eq.eq_name, eq.invnum, eq.area, query.reason, query.msg)
            return render(request, 'pc_query/success_send.html')
        except:
            return render(request, 'pc_query/fail_send.html')
    else:
        pass
    return render(request, 'pc_query/pc_query.html',
                  {'name': a, 'area1': area1, 'area2': area2, 'area3': area3, 'area4': area4, 'area5':area5, 'reasons': reasons})


@login_required
def pc_history(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT queries.query_id, queries.post_time, equipment.eq_name, queries.reason, queries.msg, "
                       "equipment.eq_status, queries.query_status, equipment.area FROM queries JOIN equipment ON (queries.eq_id = "
                       "equipment.eq_id)")
        a = cursor.fetchall()
        a = list(a)
        a.reverse()
        return render(request, 'pc_query/pc_history.html', {'dict': a})


@login_required
def delete_query(request, query_id):
    x = Queries.objects.get(query_id=query_id)
    x.delete()
    return redirect('/main')


@login_required
def settings(request):
    reasons = Reasons.objects.all()
    types = Type.objects.all()

    return render(request, 'main/settings.html', {'reasons': reasons, 'types': types})


@login_required
def add_reason(request):
    reason = request.POST.get('new_reason')
    if reason != '':
        Reasons.objects.create(reason=reason)
    return redirect('/main/settings')


@login_required
def delete_reasons(request):
    reasons = request.POST.getlist('delete_list')
    for i in reasons:
        x = Reasons.objects.get(id=i)
        x.delete()
    return redirect('/main/settings')


@login_required
def add_type(request):
    type = request.POST.get('new_type')
    if type != '':
        Type.objects.create(type=type)
    return redirect('/main/settings')


@login_required
def delete_types(request):
    types = request.POST.getlist('delete_type')
    for i in types:
        x = Type.objects.get(id=i)
        x.delete()
    return redirect('/main/settings')

def tasks(request):
    all_tasks = Daily_tasks.objects.all()
    dates = []
    for task in all_tasks:
        if task.date.date() not in dates:
            dates.append(task.date.date())
    tasks = {}
    for date in dates:
        daily_tasks = []
        for task in all_tasks:
            if task.date.date() == date:
                x = [task.task, task.status, task.task_id]
                daily_tasks.append(x)
        #tasks.append(daily_tasks)
        tasks[date] = daily_tasks
    return render(request, 'main/tasks.html', {'dates': dates, 'tasks': tasks})

def save_tasks(request):
    tasks = Daily_tasks.objects.all()
    for task in tasks:
        completed = request.POST.get(str(task.task_id))
        if completed == 'Завершена':
            a = Daily_tasks.objects.get(task_id=task.task_id)
            a.status = 'Завершена'
            a.save()
    return redirect('/main/tasks')

# Create your views here.
