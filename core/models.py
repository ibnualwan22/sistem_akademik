from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import F
from django.conf import settings
from django.utils import timezone

class Fan(models.Model):
    nama_fan = models.CharField(max_length=100, unique=True, verbose_name="Nama Fan")
    urutan = models.IntegerField(default=0, help_text="Isi dengan angka untuk urutan, misal: 1, 2, 3...")
    target_durasi_hari = models.PositiveIntegerField(default=30, help_text="Target penyelesaian dalam HARI, misal: 1 bulan = 30 hari")
    def __str__(self): return self.nama_fan

class SKS(models.Model):
    nama_sks = models.CharField(max_length=200, unique=True, verbose_name="Nama SKS/Kitab")
    fan = models.ForeignKey(Fan, on_delete=models.CASCADE, related_name='sks_list')
    nilai_minimal = models.PositiveIntegerField(default=90, help_text="Nilai minimal untuk lulus SKS ini")
    class Meta: verbose_name = "SKS"; verbose_name_plural = "SKS"
    def __str__(self): return self.nama_sks

class Pengurus(models.Model):
    nama_lengkap = models.CharField(max_length=150, verbose_name="Nama Lengkap")
    jabatan = models.CharField(max_length=100, blank=True, verbose_name="Jabatan")
    alamat_kabupaten = models.CharField(max_length=100, blank=True, verbose_name="Kabupaten/Kota")
    alamat_provinsi = models.CharField(max_length=100, blank=True, verbose_name="Provinsi")
    nomor_whatsapp = models.CharField(max_length=20, blank=True, help_text="Gunakan format internasional, contoh: 6281234567890")
    foto_profil = models.ImageField(upload_to='pengurus_photos/', blank=True, null=True)
    class Meta: verbose_name = "Pengurus"; verbose_name_plural = "Pengurus"
    def __str__(self): return self.nama_lengkap

# core/models.py

# ... (Class Fan, SKS, Pengurus tidak berubah) ...

class Santri(models.Model):
    STATUS_CHOICES = [('Aktif', 'Santri Aktif'), ('Pengurus', 'Pengurus/Abdi Dalem'), ('Non-Aktif', 'Non-Aktif/Lulusan')]
    nama_lengkap = models.CharField(max_length=150)
    id_santri = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="ID Santri")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Aktif')
    foto_profil = models.ImageField(upload_to='santri_photos/', blank=True, null=True)
    alamat_kabupaten = models.CharField(max_length=100, blank=True, verbose_name="Kabupaten/Kota")
    alamat_provinsi = models.CharField(max_length=100, blank=True, verbose_name="Provinsi")
    kamar = models.CharField(max_length=50, blank=True)
    kelas_sekolah = models.CharField(max_length=100, blank=True, verbose_name="Kelas Sekolah Formal")
    pembimbing = models.ForeignKey(Pengurus, on_delete=models.SET_NULL, null=True, blank=True, related_name='santri_bimbingan')

    class Meta:
        ordering = ['nama_lengkap']

    def __str__(self):
        return self.nama_lengkap

    # PASTIKAN METHOD INI DAN SEMUA METHOD LAIN DI BAWAHNYA MENJOROK KE DALAM SEPERTI INI
    def get_sks_lulus_ids(self):
        sks_lulus_ids = []
        for tes in self.riwayat_tes.filter(status_tes='Selesai'):
            if tes.nilai is not None:
                if tes.nilai >= tes.sks.nilai_minimal:
                    if tes.sks.id not in sks_lulus_ids:
                        sks_lulus_ids.append(tes.sks.id)
        return sks_lulus_ids

    def get_completed_fans_with_dates(self):
        sks_lulus_ids = self.get_sks_lulus_ids()
        if not sks_lulus_ids:
            return {}
        fan_completion_dates = {}
        relevant_fans = Fan.objects.filter(sks_list__id__in=sks_lulus_ids).distinct()
        for fan in relevant_fans:
            sks_in_fan_ids = set(fan.sks_list.values_list('id', flat=True))
            if not sks_in_fan_ids:
                continue
            if sks_in_fan_ids.issubset(set(sks_lulus_ids)):
                try:
                    tes_terakhir_di_fan = self.riwayat_tes.filter(
                        sks__fan=fan, status_tes='Selesai'
                    ).latest('tanggal_pelaksanaan')
                    fan_completion_dates[fan] = tes_terakhir_di_fan.tanggal_pelaksanaan
                except RiwayatTes.DoesNotExist:
                    continue
        return fan_completion_dates
    # core/models.py

# ... (Class Fan, SKS, Pengurus, Santri tidak berubah, biarkan saja) ...


# PASTIKAN CLASS DI BAWAH INI MEMILIKI INDENTASI YANG BENAR
class RiwayatTes(models.Model):
    # Baris ini menjorok 4 spasi
    STATUS_TES_CHOICES = [
        ('Terdaftar', 'Terdaftar'),
        ('Selesai', 'Selesai'),
        ('Batal', 'Batal'),
    ]

    # Semua field ini menjorok 4 spasi
    santri = models.ForeignKey(Santri, on_delete=models.CASCADE, related_name='riwayat_tes')
    sks = models.ForeignKey(SKS, on_delete=models.CASCADE, related_name='riwayat_tes')
    penguji = models.ForeignKey(Pengurus, on_delete=models.SET_NULL, null=True, blank=True, related_name='tes_diuji')
    
    tanggal_pendaftaran = models.DateField(default=timezone.now)
    tanggal_pelaksanaan = models.DateField()
    
    nilai = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    status_tes = models.CharField(max_length=10, choices=STATUS_TES_CHOICES, default='Terdaftar')

    # Method property ini menjorok 4 spasi
    @property
    def status_kelulusan(self):
        # Isinya menjorok 8 spasi
        if self.nilai is None:
            return "-"
        return "Lulus" if self.nilai >= self.sks.nilai_minimal else "Mengulang"

    # Method str ini menjorok 4 spasi
    def __str__(self):
        # Isinya menjorok 8 spasi
        return f"{self.santri.nama_lengkap} - {self.sks.nama_sks} ({self.status_tes} pada {self.tanggal_pelaksanaan})"

    # Class Meta ini menjorok 4 spasi
    class Meta:
        # Isinya menjorok 8 spasi
        ordering = ['-tanggal_pelaksanaan', '-id']