from django.shortcuts import redirect
from django.contrib import admin
from django.urls import path, include
from account.views import register
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', lambda request: redirect('account:login')),
    path('register/', register, name='home'),
    path('admin/', admin.site.urls),
    path('staff/', include('staff.urls')),
    path('account/', include('account.urls', namespace='account')),
    path('adminpanel/', include('adminpanel.urls', namespace='adminpanel')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)