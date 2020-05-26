from django.shortcuts import render, redirect
from .models import Queries, Equipment, Employees, Comment, Maintenance, Worktime, Eq_stoptime, Reasons
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

@login_required
def new_query(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT eq_name FROM equipment")
        a = cursor.fetchall()
        a = list(a)

        cursor.execute("SELECT employee_id, fio FROM employees WHERE (master = 'False')")
        emps = cursor.fetchall()
        emps = list(emps)

        area1 = list(Equipment.objects.filter(area='Механической обработки'))
        area2 = list(Equipment.objects.filter(area='Слесарный'))
        area3 = list(Equipment.objects.filter(area='Сварки'))

        reasons = Reasons.objects.all()

    if request.method == "POST":
        a1 = request.POST.get('area1')
        a2 = request.POST.get('area2')
        a3 = request.POST.get('area3')
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

            for i in doers:
                emp = Employees.objects.get(employee_id=int(i))
                send_message.send_message_4(emp.tg_id, query.query_id)
            return redirect('main')
        except Exception as ex:
            return HttpResponse(ex)

    else:
        pass
    return render(request, 'main/new_query.html',
                  {'name': a, 'emps': emps, 'area1': area1, 'area2': area2, 'area3': area3, 'reasons': reasons})

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
        result_now_emps = [int(item) for item in now_emps_list] #Преобразование "1" в 1
        now_emps = []
        for i in result_now_emps:
            e = Employees.objects.get(employee_id = i)
            now_emps.append(e)
    except:
        result_now_emps = []
        final_emps = []


    emps = Employees.objects.filter(master='False')
    for i in emps:                              # цикл подготовки массива исполнителей для корректного вывода в селект мултипл
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
        cursor.execute("SELECT worktime.query_id, worktime.start_time, worktime.stop_time, employees.fio FROM "
                       "worktime JOIN employees ON (worktime.employee_id = employees.employee_id) AND (worktime.query_id = %s)",
                       [query_id])
        works = cursor.fetchall()
        works = list(works)


    return render(request, 'main/query.html', {'query': c, 'equipment': d, 'coms': coms, 'works': works, 'emps': emps, 'now_emp': now_emp, 'final_emps': final_emps, 'reasons': reasons})

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
        funcs.appoint_doers_2(doers, query_id) # занести json файл
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
    return redirect('main')

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

    equipment = Equipment.objects.filter(eq_id=eq_id)
    name, mean, shifts = funcs.top10(equipment)
    name_m, mean_m, shifts_m = funcs.top10_month(equipment)

    return render(request, 'main/eq_one.html', {'eqs': eqs, 'queries': qs, 'name': name, 'mean': mean, 'mean_m': mean_m})

@login_required
def edit_eq(request, eq_id):
    if request.method == 'POST':
        eqs = Equipment.objects.get(eq_id=eq_id)
        eq_status = request.POST.get('eq_status_select')
        eqs.eq_status = eq_status
        eqs.shift = request.POST.get('shift_select')
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

        cursor.execute("SELECT maintenance.start_time, maintenance.employee_id, maintenance.end_time, maintenance.status, " \
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


    return render(request, 'main/edit_emp.html', {'emp': emp, 'queries': my_queries, 'done_queries': my_queries_done, 'my_tos': my_tos})

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
    names, means, sh = funcs.top10(equipment) #возвращает имена, цифры по простою и смены оборудования
    equipment = Equipment.objects.all()  # топ 10 по простою за все время
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
        to_times.append(time)
        average_time = average_time + delta
    average_time = average_time / len(to)

    return render(request, 'main/stats.html', {'go_count': go_count, 'new_count': new_count,
                                               'postpone_count': postpone_count,
                                               'got_count': got_count, 'work_count': work_count,
                                               'stop_count': stop_count,
                                               'to_count': to_count, 'names': names, 'means': means, 'shifts': sh,
                                               'names_m': names_m, 'means_m': means_m, 'shifts_m': sh_m, 'names_mech': names_mech,
                                               'means_mech': means_mech, 'shifts_mech': shifts_mech, 'names_mech_month': names_mech_month,
                                               'means_mech_month': means_mech_month, 'shifts_mech_month': shifts_mech_month,
                                               'names_smith': names_smith, 'means_smith': means_smith, 'shifts_smith': shifts_smith,
                                               'names_smith_month': names_smith_month, 'means_smith_month': means_smith_month, 'shifts_smith_month': shifts_smith_month,
                                               'names_weld': names_weld, 'means_weld': means_weld, 'shifts_weld': shifts_weld,
                                               'names_weld_month': names_weld_month, 'means_weld_month': means_weld_month, 'shifts_weld_month': shifts_weld_month,
                                               'average_time': average_time, 'to_times': to_times, 'to_names': to_names})

@login_required
def maintenance(request):
    a = list(Maintenance.objects.all())
    with connection.cursor() as cursor:
        cursor.execute("SELECT equipment.eq_name, equipment.invnum, equipment.eq_type, equipment.area, "
                       "maintenance.start_time, maintenance.employee_id, maintenance.comment, maintenance.id FROM equipment JOIN "
                       "maintenance ON (equipment.eq_id = maintenance.eq_id) and (end_time IS NULL)")

        tos = cursor.fetchall()
        tos = list(tos)
        tos.reverse()         #список с запланированными ТО


    with connection.cursor() as cursor:
        cursor.execute("SELECT equipment.eq_name, equipment.invnum, equipment.eq_type, equipment.area, "
                       "maintenance.start_time, maintenance.end_time, maintenance.employee_id, maintenance.comment, maintenance.id FROM equipment JOIN "
                       "maintenance ON (equipment.eq_id = maintenance.eq_id) and (end_time IS NOT NULL)")

        tos2 = cursor.fetchall()
        tos2 = list(tos2)
        tos2.reverse()        #список с выполнеными ТО

    return render(request, 'main/maintenance.html', {'tos': tos, 'tos2': tos2})

@login_required
def new_maintenance(request):

    with connection.cursor() as cursor:
        cursor.execute("SELECT employee_id, fio FROM employees WHERE (master = 'False')")
        emps = cursor.fetchall()
        emps = list(emps)

        area1 = list(Equipment.objects.filter(area='Механической обработки'))
        area2 = list(Equipment.objects.filter(area='Слесарный'))
        area3 = list(Equipment.objects.filter(area='Сварки'))
    if request.method == 'POST':
        #eq_id = request.POST.get('eq_name_select')
        new_date = request.POST.get('date')
        #new_emp = request.POST.get('employee_select')
        comment = request.POST.get('comment')

        a1 = request.POST.get('area1')
        a2 = request.POST.get('area2')
        a3 = request.POST.get('area3')
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

        Maintenance.objects.create(start_time=new_date, comment=comment, eq_id=eq.eq_id)

        to = Maintenance.objects.all().order_by("-id")[0]
        funcs.appoint_doers_to(doers, to.id)

        return redirect('/main/maintenance')

    return render(request, 'main/new_maintenance.html', {'emps': emps, 'area1': area1, 'area2': area2, 'area3': area3})

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

    emps = Employees.objects.filter(master='False')
    for i in emps:  # цикл подготовки массива исполнителей для корректного вывода в селект мултипл
        m = [i.employee_id, i.fio, False]
        final_emps.append(m)
        if len(result_now_emps) > 0:
            for j in result_now_emps:
                if i.employee_id == j:
                    final_emps[-1][2] = True

    return render(request, 'main/show_maintenance.html', {'eq': b, 'to': c, 'emps': emps, 'now_emp': now_emp, 'final_emps': final_emps })

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


def pc_query(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT eq_name FROM equipment")
        a = cursor.fetchall()
        a = list(a)

        area1 = list(Equipment.objects.filter(area='Механической обработки'))
        area2 = list(Equipment.objects.filter(area='Слесарный'))
        area3 = list(Equipment.objects.filter(area='Сварки'))
    if request.method == "POST":
        area1 = request.POST.get('area1')
        area2 = request.POST.get('area2')
        area3 = request.POST.get('area3')
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
    return render(request, 'pc_query/pc_query.html', {'name': a, 'area1': area1, 'area2': area2, 'area3': area3})

def pc_history(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT queries.query_id, queries.post_time, equipment.eq_name, queries.reason, queries.msg, "
                       "equipment.eq_status, queries.query_status, equipment.area FROM queries JOIN equipment ON (queries.eq_id = "
                       "equipment.eq_id)")
        a = cursor.fetchall()
        a = list(a)
        a.reverse()
        return render(request, 'pc_query/pc_history.html', {'dict': a})

def delete_query(request, query_id):
    x = Queries.objects.get(query_id=query_id)
    x.delete()
    return redirect('/main')

def settings(request):
    reasons = Reasons.objects.all()

    return render(request, 'main/settings.html', {'reasons': reasons})

def add_reason(request):
    reason = request.POST.get('new_reason')
    if reason != '':
        Reasons.objects.create(reason=reason)
    return redirect('/main/settings')

def delete_reasons(request):
    reasons = request.POST.getlist('delete_list')
    for i in reasons:
        x = Reasons.objects.get(id=i)
        x.delete()
    return redirect('/main/settings')



# Create your views here.
