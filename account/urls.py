from django.urls import path
from .views import CustomLoginView
from . import views

app_name = 'account'

urlpatterns = [
    path(
        'login/',
        CustomLoginView.as_view(
            template_name='account/login.html'
        ),
        name='login'
    ),

    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('password-reset/<uidb64>/<token>/', views.password_reset, name='password_reset'),

]