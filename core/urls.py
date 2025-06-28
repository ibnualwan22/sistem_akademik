# Lokasi file: core/urls.py
# Versi Final dan Lengkap

from django.urls import path
# Kita import seluruh modul views agar lebih aman dan jelas
from . import views

app_name = 'core'

urlpatterns = [
    # Setiap path memanggil fungsi yang benar dari 'views'
    path('accounts/login/', views.admin_login_view, name='login'),
    path('', views.daftar_santri, name='daftar_santri'),
    path('semua/', views.semua_santri_view, name='semua_santri'),
    path('sks/', views.daftar_sks_view, name='daftar_sks'),
    path('kurikulum/', views.kurikulum_view, name='kurikulum'),
    path('laporan/', views.laporan_akademik, name='laporan_akademik'),
    path('laporan/', views.laporan_akademik, name='laporan_akademik'),
    path('laporan/export-pdf/', views.export_laporan_pdf, name='export_laporan_pdf'),
    path('leaderboard/fan/<int:fan_pk>/', views.leaderboard_fan_view, name='leaderboard_fan'),
    path('<int:pk>/', views.detail_santri, name='detail_santri'),
    path('santri/<int:santri_pk>/fan/<int:fan_pk>/', views.detail_fan_santri, name='detail_fan_santri'),
    path('laporan/detail/', views.laporan_rekap_detail, name='laporan_rekap_detail'),
    path('riwayat-tes/', views.riwayat_tes_view, name='riwayat_tes'),
    path('pengurus/', views.daftar_pengurus_view, name='daftar_pengurus'),
    path('pengurus/<int:pk>/', views.detail_pengurus_view, name='detail_pengurus'),
    path('riwayat-tes/export-excel/', views.export_tes_excel, name='export_tes_excel'),
    path('pengurus/', views.daftar_pengurus_view, name='daftar_pengurus'),
    path('kontak/', views.daftar_kontak_view, name='daftar_kontak'),
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard')
]