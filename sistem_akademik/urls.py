# Lokasi file: sistem_akademik/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings               # <-- TAMBAHKAN IMPORT INI
from django.conf.urls.static import static   # <-- TAMBAHKAN IMPORT INI
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('santri/', include('core.urls')),
    path('',RedirectView.as_view(url='/santri/',permanent=False))
    
]

# --- TAMBAHKAN BLOK INI DI PALING BAWAH ---
# Ini hanya untuk mode development (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)