# Lokasi file: core/admin.py
# Versi Final dengan Fitur Inlines

from django.contrib import admin
from .models import Fan, SKS, Santri, RiwayatTes

# --- Konfigurasi Inline untuk Riwayat Tes ---
class RiwayatTesInline(admin.TabularInline):
    model = RiwayatTes
    # Sediakan 1 baris kosong tambahan untuk entri baru
    extra = 1 
    # Tampilkan hanya field ini agar tidak terlalu ramai
    fields = ('sks', 'nilai', 'tanggal_tes')
    # Fitur autocomplete untuk SKS jika daftarnya sangat banyak
    autocomplete_fields = ('sks',)

# --- Konfigurasi untuk Halaman Admin Santri ---
@admin.register(Santri)
class SantriAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'status', 'id_santri')
    list_filter = ('status',)
    search_fields = ('nama_lengkap', 'id_santri')
    # 'inlines' adalah perintah untuk memasukkan RiwayatTesInline ke halaman ini
    inlines = [RiwayatTesInline]

# --- Konfigurasi untuk Halaman Admin SKS ---
@admin.register(SKS)
class SKSAdmin(admin.ModelAdmin):
    list_display = ('nama_sks', 'fan', 'nilai_minimal')
    list_editable = ('fan', 'nilai_minimal')
    list_filter = ('fan',)
    search_fields = ('nama_sks',)
    # Aktifkan kotak pencarian untuk ForeignKey Fan
    autocomplete_fields = ('fan',)

# --- Konfigurasi untuk Halaman Admin Fan ---
@admin.register(Fan)
class FanAdmin(admin.ModelAdmin):
    list_display = ('nama_fan', 'urutan', 'target_durasi_hari')
    list_editable = ('urutan', 'target_durasi_hari')
    search_fields = ('nama_fan',)

# --- Konfigurasi untuk Halaman Admin Riwayat Tes (Halaman terpisah) ---
@admin.register(RiwayatTes)
class RiwayatTesAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'nilai', 'status_kelulusan', 'tanggal_tes')
    list_filter = ('santri', 'sks__fan', 'tanggal_tes')
    search_fields = ('santri__nama_lengkap', 'sks__nama_sks')
    autocomplete_fields = ('santri', 'sks')