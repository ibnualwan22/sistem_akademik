from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import F
from django.conf import settings

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

class Santri(models.Model):
    STATUS_CHOICES = [('Aktif', 'Santri Aktif'), ('Pengurus', 'Pengurus/Abdi Dalem'), ('Non-Aktif', 'Non-Aktif/Lulusan')]
    nama_lengkap = models.CharField(max_length=150)
    id_santri = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="ID Santri")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Aktif')
    foto_profil = models.ImageField(upload_to='santri_photos/', blank=True, null=True)
    alamat_kabupaten = models.CharField(max_length=100, blank=True, verbose_name="Kabupaten/Kota")
    alamat_provinsi = models.CharField(max_length=100, blank=True, verbose_name="Provinsi")
    kamar = models.CharField(max_length=50, blank=True)
    kelas_sekolah = models.CharField(max_length=100, blank=True, verbose_name="Kelas Sekolah Formal")
    pembimbing = models.ForeignKey(Pengurus, on_delete=models.SET_NULL, null=True, blank=True, related_name='santri_bimbingan')
    def __str__(self): return self.nama_lengkap
    def get_sks_lulus_ids(self):
        sks_lulus_ids = []
        for tes in self.riwayat_tes.select_related('sks').all():
            if tes.nilai >= tes.sks.nilai_minimal:
                if tes.sks.id not in sks_lulus_ids: sks_lulus_ids.append(tes.sks.id)
        return sks_lulus_ids
    def get_completed_fans_with_dates(self):
        sks_lulus_ids = self.get_sks_lulus_ids()
        if not sks_lulus_ids:
            return {}
        
        # Semua logika ini seharusnya berada di dalam method ini
        fan_completion_dates = {}
        relevant_fans = Fan.objects.filter(sks_list__id__in=sks_lulus_ids).distinct()

        for fan in relevant_fans:
            sks_in_fan = fan.sks_list.all()
            if all(sks.id in sks_lulus_ids for sks in sks_in_fan):
                try:
                    tgl_selesai = self.riwayat_tes.filter(sks__fan=fan).latest('tanggal_tes').tanggal_tes
                    fan_completion_dates[fan] = tgl_selesai
                except RiwayatTes.DoesNotExist:
                    continue
        
        return fan_completion_dates    

class RiwayatTes(models.Model):
    santri = models.ForeignKey(Santri, on_delete=models.CASCADE, related_name='riwayat_tes')
    sks = models.ForeignKey(SKS, on_delete=models.CASCADE, related_name='riwayat_tes')
    tanggal_tes = models.DateField()
    nilai = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    @property
    def status_kelulusan(self): return "Lulus" if self.nilai >= self.sks.nilai_minimal else "Mengulang"
    def __str__(self): return f"{self.santri.nama_lengkap} - {self.sks.nama_sks} ({self.status_kelulusan})"
