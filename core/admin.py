# core/admin.py

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from datetime import date

from .models import (
    Asrama, UserProfile, Fan, SKS, Santri,
    RiwayatTes, Pengurus, GrupKontak, KontakPerson
)

# KELAS FILTER KUSTOM (jika ada, seperti StatusKelulusanFilter)
class StatusKelulusanFilter(admin.SimpleListFilter):
    title = 'Status Kelulusan'
    parameter_name = 'status_kelulusan'
    def lookups(self, request, model_admin): return (('lulus', 'Lulus'), ('mengulang', 'Mengulang'),)
    def queryset(self, request, queryset):
        if self.value() == 'lulus': return queryset.filter(id__in=[tes.id for tes in queryset if tes.status_kelulusan == 'Lulus'])
        if self.value() == 'mengulang': return queryset.filter(id__in=[tes.id for tes in queryset if tes.status_kelulusan == 'Mengulang'])

# KELAS DASAR KEBIJAKAN ABAC UNTUK ADMIN
class AsramaScopedAdmin(admin.ModelAdmin):
    def get_exclude(self, request, obj=None):
        if not request.user.is_superuser:
            return ['asrama']
        return super().get_exclude(request, obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            return qs.filter(asrama=request.user.profile.asrama)
        except (UserProfile.DoesNotExist, AttributeError):
            return qs.none()

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            try:
                if not obj.asrama_id:
                    obj.asrama = request.user.profile.asrama
            except (UserProfile.DoesNotExist, AttributeError):
                pass
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            try:
                asrama_pengguna = request.user.profile.asrama
                if hasattr(db_field.related_model, 'asrama'):
                    kwargs['queryset'] = db_field.related_model.objects.filter(asrama=asrama_pengguna)
            except (UserProfile.DoesNotExist, AttributeError):
                kwargs['queryset'] = db_field.related_model.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# PENDAFTARAN MODEL-MODEL KE ADMIN PANEL
@admin.register(Asrama)
class AsramaAdmin(admin.ModelAdmin):
    list_display = ('nama_asrama', 'id_asrama_unik', 'is_active')
    search_fields = ('nama_asrama', 'id_asrama_unik')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'asrama')
    list_filter = ('asrama',)
    autocomplete_fields = ('user', 'asrama')

@admin.register(Fan)
class FanAdmin(AsramaScopedAdmin):
    list_display = ('nama_fan', 'urutan', 'target_durasi_hari', 'asrama')
    search_fields = ('nama_fan',)
    ordering = ('urutan',)
    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ('asrama',)
        return ()

@admin.register(SKS)
class SKSAdmin(AsramaScopedAdmin):
    list_display = ('nama_sks', 'fan', 'nilai_minimal', 'asrama')
    search_fields = ('nama_sks',)
    autocomplete_fields = ('fan',)
    list_filter = ('fan',)
    def get_list_filter(self, request):
        base_filters = list(super().get_list_filter(request))
        if request.user.is_superuser:
            base_filters.append('asrama')
        return tuple(base_filters)

@admin.register(Santri)
class SantriAdmin(AsramaScopedAdmin):
    list_display = ('nama_lengkap', 'id_santri', 'status', 'asrama')
    search_fields = ('nama_lengkap', 'id_santri')
    list_per_page = 20
    autocomplete_fields = ('pembimbing',)
    list_filter = ('status',)
    def get_list_filter(self, request):
        base_filters = list(super().get_list_filter(request))
        if request.user.is_superuser:
            base_filters.append('asrama')
        return tuple(base_filters)

@admin.register(RiwayatTes)
class RiwayatTesAdmin(AsramaScopedAdmin):
    list_display = ('get_nama_santri', 'get_nama_sks', 'tanggal_pelaksanaan', 'penguji', 'status_tes', 'status_kelulusan')
    list_filter = ('status_tes', 'tanggal_pelaksanaan', 'sks__fan', 'penguji', StatusKelulusanFilter)
    search_fields = ('santri__nama_lengkap', 'sks__nama_sks', 'penguji__nama_lengkap')
    autocomplete_fields = ('santri', 'sks', 'penguji')
    def get_list_filter(self, request):
        base_filters = list(super().get_list_filter(request))
        if request.user.is_superuser:
            base_filters.insert(0, ('sks__fan__asrama', admin.RelatedOnlyFieldListFilter))
        return tuple(base_filters)
    @admin.display(description='Nama Santri', ordering='santri__nama_lengkap')
    def get_nama_santri(self, obj): return obj.santri.nama_lengkap
    @admin.display(description='SKS / Kitab', ordering='sks__nama_sks')
    def get_nama_sks(self, obj): return obj.sks.nama_sks

@admin.register(Pengurus)
class PengurusAdmin(AsramaScopedAdmin):
    list_display = ('nama_lengkap', 'jabatan', 'nomor_whatsapp', 'asrama')
    search_fields = ('nama_lengkap', 'jabatan')
    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ('asrama',)
        return ()

@admin.register(GrupKontak)
class GrupKontakAdmin(AsramaScopedAdmin):
    list_display = ('nama_grup', 'urutan', 'asrama')
    search_fields = ('nama_grup',)
    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ('asrama',)
        return ()

@admin.register(KontakPerson)
class KontakPersonAdmin(AsramaScopedAdmin):
    list_display = ('nama_lengkap', 'grup', 'keterangan', 'nomor_whatsapp', 'email', 'asrama')
    search_fields = ('nama_lengkap', 'keterangan')
    autocomplete_fields = ('grup',)
    list_filter = ('grup',)
    def get_list_filter(self, request):
        base_filters = list(super().get_list_filter(request))
        if request.user.is_superuser:
            base_filters.append(('grup__asrama', admin.RelatedOnlyFieldListFilter))
        return tuple(base_filters)
    
@admin.register(LogEntry)
class LogEntryAdmin(AsramaScopedAdmin):
    readonly_fields = ('action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message')
    list_display = ('action_time', 'user', 'get_action_description', 'object_repr', 'get_content_type')
    list_filter = ('action_time', 'user', 'content_type')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    @admin.display(description='Objek')
    def get_content_type(self, obj): return obj.content_type.name
    @admin.display(description='Aksi', ordering='action_flag')
    def get_action_description(self, obj): return {1: "➕ Penambahan", 2: "✏️ Perubahan", 3: "❌ Penghapusan"}.get(obj.action_flag, '-')
