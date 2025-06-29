# core/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import F
from django.conf import settings
from django.utils import timezone

# 1. MODEL PUSAT UNTUK TENANT/ASRAMA
class Asrama(models.Model):
    nama_asrama = models.CharField(max_length=150, unique=True, verbose_name="Nama Asrama")
    id_asrama_unik = models.CharField(max_length=50, unique=True, help_text="ID unik untuk login, contoh: takhossus_pusat")
    alamat = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="Aktif")

    def __str__(self):
        return self.nama_asrama
    class Meta:
        verbose_name = "Data Asrama"
        verbose_name_plural = "Data Asrama"
        ordering = ['nama_asrama']

# 2. MODEL UNTUK MEMBERI ATRIBUT 'ASRAMA' KE PENGGUNA (USER)
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    asrama = models.ForeignKey(Asrama, on_delete=models.SET_NULL, null=True, blank=True, help_text="Asrama tempat user ini bertugas. Kosongkan untuk superuser.")

    def __str__(self):
        return f"Profil untuk {self.user.username}"

# 3. MENAMBAHKAN ATRIBUT 'ASRAMA' KE SEMUA MODEL DATA LAINNYA
# (null=True ditambahkan untuk kemudahan migrasi data yang sudah ada)

class Fan(models.Model):
    asrama = models.ForeignKey(Asrama, on_delete=models.CASCADE, related_name='fans', null=True)
    nama_fan = models.CharField(max_length=100, verbose_name="Nama Fan")
    urutan = models.IntegerField(default=0, help_text="Isi dengan angka untuk urutan, misal: 1, 2, 3...")
    target_durasi_hari = models.PositiveIntegerField(default=30, help_text="Target penyelesaian dalam HARI, misal: 1 bulan = 30 hari")
    def __str__(self): return self.nama_fan
    class Meta:
        ordering = ['urutan']

class SKS(models.Model):
    asrama = models.ForeignKey(Asrama, on_delete=models.CASCADE, related_name='sks_list', null=True)
    nama_sks = models.CharField(max_length=200, verbose_name="Nama SKS/Kitab")
    fan = models.ForeignKey(Fan, on_delete=models.CASCADE, related_name='sks_list')
    nilai_minimal = models.PositiveIntegerField(default=90, help_text="Nilai minimal untuk lulus SKS ini")
    class Meta:
        verbose_name = "SKS"
        verbose_name_plural = "SKS"
        ordering = ['fan__urutan', 'nama_sks']
    def __str__(self): return self.nama_sks

class Pengurus(models.Model):
    asrama = models.ForeignKey(Asrama, on_delete=models.CASCADE, related_name='pengurus_list', null=True)
    nama_lengkap = models.CharField(max_length=150, verbose_name="Nama Lengkap")
    jabatan = models.CharField(max_length=100, blank=True, verbose_name="Jabatan")
    nomor_whatsapp = models.CharField(max_length=20, blank=True, help_text="Gunakan format internasional, contoh: 6281234567890")
    foto_profil = models.ImageField(upload_to='pengurus_photos/', blank=True, null=True)
    class Meta:
        verbose_name = "Pengurus"
        verbose_name_plural = "Pengurus"
        ordering = ['nama_lengkap']
    def __str__(self): return self.nama_lengkap

class Santri(models.Model):
    asrama = models.ForeignKey(Asrama, on_delete=models.CASCADE, related_name='santri_list', null=True)
    STATUS_CHOICES = [('Aktif', 'Santri Aktif'), ('Pengurus', 'Pengurus/Abdi Dalem'), ('Non-Aktif', 'Non-Aktif/Lulusan')]
    nama_lengkap = models.CharField(max_length=150)
    id_santri = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="ID Santri")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Aktif')
    foto_profil = models.ImageField(upload_to='santri_photos/', blank=True, null=True)
    pembimbing = models.ForeignKey(Pengurus, on_delete=models.SET_NULL, null=True, blank=True, related_name='santri_bimbingan')
    class Meta:
        ordering = ['nama_lengkap']
    def __str__(self):
        return self.nama_lengkap
    def get_sks_lulus_ids(self):
        return list(self.riwayat_tes.filter(nilai__gte=F('sks__nilai_minimal')).values_list('sks_id', flat=True).distinct())
    # Letakkan method yang sudah diperbaiki ini di dalam class Santri

    def get_completed_fans_with_dates(self):
        # Pastikan kita punya model Fan di scope ini
        from .models import Fan, RiwayatTes 

        sks_lulus_ids = self.get_sks_lulus_ids()
        
        # [FIXED] Baris ini yang sebelumnya error
        if not sks_lulus_ids:
            return {}

        fan_completion_dates = {}
        # Filter Fan berdasarkan asrama dari santri yang bersangkutan untuk keamanan
        relevant_fans = Fan.objects.filter(asrama=self.asrama, sks_list__id__in=sks_lulus_ids).distinct()

        for fan in relevant_fans:
            sks_in_fan_ids = set(fan.sks_list.values_list('id', flat=True))
            if not sks_in_fan_ids or not sks_in_fan_ids.issubset(set(sks_lulus_ids)):
                continue

            try:
                # Ambil tes terakhir untuk fan yang sudah komplit
                tes_terakhir_di_fan = self.riwayat_tes.filter(
                    sks__fan=fan, status_tes='Selesai'
                ).latest('tanggal_pelaksanaan')
                fan_completion_dates[fan] = tes_terakhir_di_fan.tanggal_pelaksanaan
            except RiwayatTes.DoesNotExist:
                continue

        return fan_completion_dates
    

class RiwayatTes(models.Model):
    asrama = models.ForeignKey(Asrama, on_delete=models.CASCADE, related_name='tes_list', null=True)
    STATUS_TES_CHOICES = [('Terdaftar', 'Terdaftar'), ('Selesai', 'Selesai'), ('Batal', 'Batal')]
    santri = models.ForeignKey(Santri, on_delete=models.CASCADE, related_name='riwayat_tes')
    sks = models.ForeignKey(SKS, on_delete=models.CASCADE, related_name='riwayat_tes')
    penguji = models.ForeignKey(Pengurus, on_delete=models.SET_NULL, null=True, blank=True, related_name='tes_diuji')
    tanggal_pendaftaran = models.DateField(default=timezone.now)
    tanggal_pelaksanaan = models.DateField()
    nilai = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    status_tes = models.CharField(max_length=10, choices=STATUS_TES_CHOICES, default='Terdaftar')
    @property
    def status_kelulusan(self):
        if self.nilai is None: return "-"
        return "Lulus" if self.nilai >= self.sks.nilai_minimal else "Mengulang"
    def __str__(self): return f"{self.santri.nama_lengkap} - {self.sks.nama_sks}"
    class Meta:
        ordering = ['-tanggal_pelaksanaan', '-id']

class GrupKontak(models.Model):
    asrama = models.ForeignKey(Asrama, on_delete=models.CASCADE, related_name='grup_kontak_list', null=True)
    nama_grup = models.CharField(max_length=100, verbose_name="Nama Grup Kontak")
    urutan = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['urutan']
        verbose_name = "Grup Kontak"
        verbose_name_plural = "Grup Kontak"
    def __str__(self): return self.nama_grup

class KontakPerson(models.Model):
    asrama = models.ForeignKey(Asrama, on_delete=models.CASCADE, related_name='kontak_person_list', null=True)
    grup = models.ForeignKey(GrupKontak, on_delete=models.CASCADE, related_name="kontak_list")
    nama_lengkap = models.CharField(max_length=150)
    keterangan = models.CharField(max_length=150)
    nomor_whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, null=True)
    foto_profil = models.ImageField(upload_to='kontak_photos/', blank=True, null=True)
    class Meta:
        ordering = ['nama_lengkap']
        verbose_name = "Kontak Person"
        verbose_name_plural = "Kontak Person"
    def __str__(self): return self.nama_lengkap