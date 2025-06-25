# core/admin.py - VERSI FINAL DENGAN CUSTOM FILTER

from django.contrib import admin
from .models import Fan, SKS, Santri, RiwayatTes, Pengurus

# Filter custom untuk status kelulusan
class StatusKelulusanFilter(admin.SimpleListFilter):
    title = 'Status Kelulusan' # Judul filter di sidebar
    parameter_name = 'status_kelulusan' # Nama parameter di URL

    def lookups(self, request, model_admin):
        # Opsi yang akan muncul di filter
        return (
            ('lulus', 'Lulus'),
            ('mengulang', 'Mengulang'),
        )

    def queryset(self, request, queryset):
        # Logika untuk mem-filter data
        if self.value() == 'lulus':
            # Ambil ID tes yang nilainya memenuhi syarat
            lulus_ids = [tes.id for tes in queryset if tes.status_kelulusan == 'Lulus']
            return queryset.filter(id__in=lulus_ids)
        if self.value() == 'mengulang':
            # Ambil ID tes yang nilainya TIDAK memenuhi syarat
            mengulang_ids = [tes.id for tes in queryset if tes.status_kelulusan == 'Mengulang']
            return queryset.filter(id__in=mengulang_ids)


@admin.register(Fan)
class FanAdmin(admin.ModelAdmin):
    list_display = ('nama_fan', 'urutan', 'target_durasi_hari')
    search_fields = ('nama_fan',)
    ordering = ('urutan',)

@admin.register(SKS)
class SKSAdmin(admin.ModelAdmin):
    list_display = ('nama_sks', 'fan', 'nilai_minimal')
    list_filter = ('fan',)
    search_fields = ('nama_sks',)
    autocomplete_fields = ('fan',)

@admin.register(Santri)
class SantriAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'id_santri', 'status')
    list_filter = ('status',)
    search_fields = ('nama_lengkap', 'id_santri')
    list_per_page = 20
    
@admin.register(RiwayatTes)
class RiwayatTesAdmin(admin.ModelAdmin):
    list_display = ('get_nama_santri', 'get_nama_sks', 'tanggal_tes', 'nilai', 'status_kelulusan')
    # Menggunakan filter custom yang baru kita buat
    list_filter = ('tanggal_tes', 'sks__fan', StatusKelulusanFilter)
    search_fields = ('santri__nama_lengkap', 'sks__nama_sks')
    autocomplete_fields = ('santri', 'sks')
    list_per_page = 25

    @admin.display(description='Nama Santri', ordering='santri__nama_lengkap')
    def get_nama_santri(self, obj):
        return obj.santri.nama_lengkap

    @admin.display(description='SKS / Kitab', ordering='sks__nama_sks')
    def get_nama_sks(self, obj):
        return obj.sks.nama_sks
    
@admin.register(Pengurus)
class PengurusAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'jabatan', 'nomor_whatsapp')
    search_fields = ('nama_lengkap', 'jabatan')