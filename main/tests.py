from django.test import TestCase

# Create your tests here.
for i in a:
    if (i.start_time.month != i.plan_date.month) and i.start_time:
        if i.end_time:
            delta = i.start_time - i.plan_date
            i.status2 = 'Выполнено с опозданием ' + str(delta.days) + ' дней'
            i.save()
    elif not i.start_time:
        if i.plan_date.month != datetime.now().month:
            delta = datetime.now().month - i.plan_date.month
            i.status2 = 'Просрочено на ' + str(delta.days) + ' дней'