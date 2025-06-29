# Lokasi file: core/urls.py
# Versi Final yang Sudah Diperbaiki dan Dirapikan

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # URL Halaman Utama/Dashboard
    path('', views.daftar_santri, name='daftar_santri'),

    # URL yang Berhubungan dengan Santri
    path('santri/semua/', views.semua_santri_view, name='semua_santri'),
    path('santri/<int:pk>/', views.detail_santri, name='detail_santri'),
    path('santri/<int:santri_pk>/fan/<int:fan_pk>/', views.detail_fan_santri, name='detail_fan_santri'),

    # URL yang Berhubungan dengan Kurikulum & Akademik
    path('sks/', views.daftar_sks_view, name='daftar_sks'),
    path('kurikulum/', views.kurikulum_view, name='kurikulum'),
    path('leaderboard/fan/<int:fan_pk>/', views.leaderboard_fan_view, name='leaderboard_fan'),
    path('riwayat-tes/', views.riwayat_tes_view, name='riwayat_tes'),
    path('riwayat-tes/export-excel/', views.export_tes_excel, name='export_tes_excel'),

    # URL yang Berhubungan dengan Laporan
    path('laporan/akademik/', views.laporan_akademik, name='laporan_akademik'),
    path('laporan/detail/', views.laporan_rekap_detail, name='laporan_rekap_detail'),
    path('laporan/export-pdf/', views.export_laporan_pdf, name='export_laporan_pdf'),

    # URL yang Berhubungan dengan Pengurus dan Kontak
    path('pengurus/', views.daftar_pengurus_view, name='daftar_pengurus'),
    path('pengurus/<int:pk>/', views.detail_pengurus_view, name='detail_pengurus'),
    path('kontak/', views.daftar_kontak_view, name='daftar_kontak'),

    # (URL untuk custom admin login, bisa dihapus jika tidak digunakan secara spesifik)
    path('accounts/login/', views.admin_login_view, name='login'),
]