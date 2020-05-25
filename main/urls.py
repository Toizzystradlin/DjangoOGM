from django.urls import path
from django.views.generic import ListView, DetailView
from main.models import Queries
from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('<int:query_id>/', views.show_query, name='show_query'),
    path('new_query', views.new_query, name='new_query'),
    path('<int:query_id>/edit_query', views.edit_query, name='edit_query'),
    path('equipment', views.show_equipment, name='show_equipment'),
    path('equipment/<int:eq_id>', views.show_eq, name='show_eq'),
    path('equipment/<int:eq_id>/q', views.edit_eq, name='edit_eq'),
    path('equipment/new_eq', views.new_eq, name='eq_create'),
    path('employees', views.show_employees, name='show_employees'),
    path('employees/<int:employee_id>', views.show_emp, name='show_emp'),
    path('employees/add_new', views.add_new, name='add_new'),
    path('employees/add_new/save_emp', views.save_emp, name='save_emp'),
    path('stats', views.stats, name='stats'),
    path('maintenance', views.maintenance, name='maintenance'),
    path('maintenance/new_maintenance', views.new_maintenance, name='new_maintenance'),
    path('main/maintenance/new_maintenance/new_maintenance_save', views.new_maintenance, name='new_maintenance_save'),
    path('maintenance/<int:maintenance_id>', views.show_maintenance, name='show_maintenance'),
    path('main/maintenance/new_maintenance/maintenance_edit', views.maintenance_edit, name='maintenance_edit'),
    path('main/maintenance/new_maintenance/<int:to_id>/maintenance_edit', views.maintenance_edit, name='maintenance_edit'),
    path('pc_query/pc_query', views.pc_query, name='pc_query'),
    path('pc_query/pc_history', views.pc_history, name='pc_history'),
    path('<int:query_id>/delete_query', views.delete_query, name='delete_query'),
    path('settings', views.settings, name='settings'),
    path('main/settings/add_reason', views.add_reason, name='add_reason'),
    path('delete_reasons', views.delete_reasons, name='delete_reasons'),
]
