# sistem_akademik/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import asrama_login_view, asrama_logout_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # PASTIKAN HANYA ADA SATU BARIS 'include' UNTUK 'core.urls'
    path('app/', include('core.urls')),

    # URL untuk login dan logout
    path('', asrama_login_view, name='asrama_login'),
    path('logout/', asrama_logout_view, name='asrama_logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)