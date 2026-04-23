from django.urls import path
from . import views

urlpatterns = [
    path('staff-dashboard', views.staff_dashboard, name='staff_dashboard'),
    path('submit-sale/', views.submit_inventory, name='submit_inventory'),
    path('my-reports/', views.my_reports, name='my_reports'),
    path("report/<int:id>/", views.view_report, name="view_report"),
    path("report/<int:id>/edit/", views.edit_report, name="edit_report"),
    path("report/<int:id>/delete/", views.delete_report, name="delete_report"),
]