from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('update-dispatch/', views.update_dispatch, name='update_dispatch'),
    path('add-cluster/', views.add_cluster, name='add_cluster'),
    path('add-station/', views.add_station, name='add_station'),
    path('assign-user/', views.assign_user, name='assign_user'),
    path('user-list/', views.user_list, name='user_list'),
    path('activate/<int:user_id>/', views.activate, name='activate'),
    path('deactivate/<int:user_id>/', views.deactivate, name='deactivate'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('delete-report/<int:id>/', views.delete_report, name='delete_report'),
    path('all-reports/', views.all_reports, name='all_reports'),
    path('toggle-read/<int:id>/', views.toggle_read, name='toggle_read'),
    path('notifications/', views.notification, name='notifications'),
    path('mark-as-read/<int:notif_id>/', views.mark_as_read, name='mark_as_read'),
    path('mark-all-as-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('read-toggle/<int:id>/', views.read_toggle, name='read_toggle'),
    path('station-list/', views.station_list, name="station_list"),
    path('delete-station/<int:id>/', views.delete_station, name='delete_station'),
    path('edit-station/<int:id>/', views.edit_station, name='edit_station'),
]