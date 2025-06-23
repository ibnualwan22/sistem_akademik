# core/migrations/000X_ubah_status_lulus_ke_pengurus.py

from django.db import migrations

def ubah_nilai_status(apps, schema_editor):
    # Fungsi ini akan mencari semua santri dengan status 'Lulus' dan mengubahnya menjadi 'Pengurus'
    Santri = apps.get_model('core', 'Santri')
    Santri.objects.filter(status='Lulus').update(status='Pengurus')

class Migration(migrations.Migration):

    dependencies = [
        # GANTI INI dengan nama file migrasi terakhir Anda sebelumnya
        ('core', '0005_santri_foto_profil'), 
    ]

    operations = [
        migrations.RunPython(ubah_nilai_status),
    ]