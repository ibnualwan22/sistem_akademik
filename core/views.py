# Lokasi file: core/views.py
# Versi FINAL LENGKAP dengan SEMUA FUNGSI - 22 Juni 2025

from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q, F, Max, Min, Avg
from .models import Santri, RiwayatTes, SKS, Fan
from datetime import date, timedelta
import json
# core/views.py
import logging

logger = logging.getLogger(__name__)  # __name__ otomatis = 'core.views'


# ==============================================================================
# FUNGSI 1: DASHBOARD UTAMA
# ==============================================================================
def daftar_santri(request):
    total_santri_aktif = Santri.objects.filter(status='Aktif').count()
    total_lulusan = Santri.objects.filter(status='Lulus').count()
    total_sks = SKS.objects.count()
    today = date.today()
    aktivitas_terkini = RiwayatTes.objects.filter(tanggal_tes=today).order_by('-id')
    
    semua_fan = Fan.objects.all().order_by('urutan')
    juara_per_fan = []
    for fan in semua_fan:
        peringkat_fan = Santri.objects.filter(status='Aktif', riwayat_tes__sks__fan=fan).annotate(
            jumlah_lulus_di_fan=Count('riwayat_tes__sks', distinct=True, filter=Q(riwayat_tes__sks__fan=fan) & Q(riwayat_tes__nilai__gte=F('riwayat_tes__sks__nilai_minimal')))
        ).filter(jumlah_lulus_di_fan__gt=0).order_by('-jumlah_lulus_di_fan', 'id')
        juara = peringkat_fan.first()
        if juara:
            juara_per_fan.append({'fan': fan, 'santri': juara, 'jumlah_lulus': juara.jumlah_lulus_di_fan})
            
    mvp_santri = Santri.objects.filter(
        status='Aktif',
        riwayat_tes__tanggal_tes__gte=today - timedelta(days=7),
    ).annotate(
        lulus_mingguan=Count('riwayat_tes', filter=Q(riwayat_tes__nilai__gte=F('riwayat_tes__sks__nilai_minimal')))
    ).order_by('-lulus_mingguan').first()

    konteks = { 'page_title': 'Dashboard Utama', 'total_santri_aktif': total_santri_aktif, 'total_lulusan': total_lulusan, 'total_sks': total_sks, 'aktivitas_terkini': aktivitas_terkini, 'juara_per_fan': juara_per_fan, 'mvp_santri': mvp_santri }
    return render(request, 'core/daftar_santri.html', konteks)

# ==============================================================================
# FUNGSI 2: HALAMAN DAFTAR SEMUA SANTRI (DENGAN PENCARIAN)
# ==============================================================================
def semua_santri_view(request):
    query = request.GET.get('q')
    santri_aktif_list = Santri.objects.filter(status='Aktif')
    santri_lulus_list = Santri.objects.filter(status='Lulus')
    santri_nonaktif_list = Santri.objects.filter(status='Non-Aktif')
    if query:
        santri_aktif_list = santri_aktif_list.filter(nama_lengkap__icontains=query)
        santri_lulus_list = santri_lulus_list.filter(nama_lengkap__icontains=query)
        santri_nonaktif_list = santri_nonaktif_list.filter(nama_lengkap__icontains=query)
    konteks = {
        'page_title': 'Daftar Lengkap Santri',
        'santri_aktif_list': santri_aktif_list.order_by('nama_lengkap'),
        'santri_lulus_list': santri_lulus_list.order_by('nama_lengkap'),
        'santri_nonaktif_list': santri_nonaktif_list.order_by('nama_lengkap'),
    }
    return render(request, 'core/semua_santri.html', konteks)

# ==============================================================================
# FUNGSI 3: HALAMAN PROFIL DAN DASHBOARD DETAIL PER SANTRI
# ==============================================================================
def detail_santri(request, pk):
    santri = get_object_or_404(Santri, pk=pk)
    semua_tes_santri = santri.riwayat_tes.select_related('sks__fan').all()
    semua_fan = Fan.objects.all().order_by('urutan')
    sks_lulus_ids = santri.get_sks_lulus_ids()

    fan_completion_dates = {}
    for fan_item in semua_fan:
        sks_in_fan_ids = SKS.objects.filter(fan=fan_item).values_list('id', flat=True)
        lulus_in_fan_ids = set(sks_lulus_ids).intersection(set(sks_in_fan_ids))
        if len(sks_in_fan_ids) > 0 and len(lulus_in_fan_ids) == len(sks_in_fan_ids):
            try:
                latest_test = semua_tes_santri.filter(sks_id__in=lulus_in_fan_ids).latest('tanggal_tes')
                fan_completion_dates[fan_item.id] = latest_test.tanggal_tes
            except RiwayatTes.DoesNotExist: pass

    progress_per_fan = []
    for fan in semua_fan:
        sks_dalam_fan = SKS.objects.filter(fan=fan)
        total_sks_di_fan = sks_dalam_fan.count()
        sks_lulus_di_fan = sks_dalam_fan.filter(id__in=sks_lulus_ids)
        jumlah_lulus_di_fan = sks_lulus_di_fan.count()
        sks_belum_lulus_di_fan = sks_dalam_fan.exclude(id__in=sks_lulus_ids)
        persentase = round((jumlah_lulus_di_fan / total_sks_di_fan) * 100) if total_sks_di_fan > 0 else 0
        
        durasi_studi, status_target, tanggal_mulai, tanggal_selesai, selisih_hari_int = None, None, None, fan_completion_dates.get(fan.id), None
        if fan.urutan == 1:
            if semua_tes_santri.exists():
                try:
                    tanggal_mulai = min(tes.tanggal_tes for tes in semua_tes_santri)
                except ValueError: pass
        else:
            try:
                fan_sebelumnya = Fan.objects.get(urutan=fan.urutan - 1)
                tanggal_mulai = fan_completion_dates.get(fan_sebelumnya.id)
            except Fan.DoesNotExist: pass
        if tanggal_mulai and tanggal_selesai:
            selisih_hari_int = (tanggal_selesai - tanggal_mulai).days
            durasi_studi = f"{selisih_hari_int if selisih_hari_int > 0 else 1} hari" if selisih_hari_int < 30 else f"{selisih_hari_int // 30} bulan, {selisih_hari_int % 30} hari"
            if fan.target_durasi_hari > 0 and selisih_hari_int is not None:
                status_target = "Sesuai Target" if selisih_hari_int <= fan.target_durasi_hari else "Melebihi Target"
        progress_per_fan.append({'fan': fan, 'total_sks': total_sks_di_fan,'jumlah_lulus': jumlah_lulus_di_fan, 'persentase': persentase, 'durasi_studi': durasi_studi, 'status_target': status_target, 'sks_lulus': sks_lulus_di_fan, 'sks_belum_lulus': sks_belum_lulus_di_fan})
    
    fan_saat_ini = next((data['fan'] for data in progress_per_fan if data['persentase'] < 100), None)
    if not fan_saat_ini and progress_per_fan:
        total_durasi_teks = "N/A"
        if fan_completion_dates and semua_tes_santri.exists():
            try:
                tanggal_paling_akhir, tanggal_paling_awal = max(fan_completion_dates.values()), min(tes.tanggal_tes for tes in semua_tes_santri)
                total_durasi_hari = (tanggal_paling_akhir - tanggal_paling_awal).days
                total_durasi_teks = f"{total_durasi_hari // 30} bulan, {total_durasi_hari % 30} hari" if total_durasi_hari >= 30 else f"{total_durasi_hari} hari"
            except ValueError: total_durasi_teks = "Data tidak cukup"
        fan_saat_ini = f"Selamat! Anda telah menyelesaikan Program Takhossus dengan total durasi {total_durasi_teks}"
    
    konteks = {'santri': santri, 'progress_per_fan': progress_per_fan, 'semua_tes': semua_tes_santri.order_by('-tanggal_tes'), 'fan_saat_ini': fan_saat_ini, 'page_title': f'Profil {santri.nama_lengkap}'}
    return render(request, 'core/detail_santri.html', konteks)

# ==============================================================================
# FUNGSI 4: HALAMAN DETAIL SKS PER FAN
# ==============================================================================
def detail_fan_santri(request, santri_pk, fan_pk):
    santri = get_object_or_404(Santri, pk=santri_pk)
    fan = get_object_or_404(Fan, pk=fan_pk)
    sks_lulus_ids = santri.get_sks_lulus_ids()
    sks_dalam_fan = SKS.objects.filter(fan=fan)
    sks_lulus = sks_dalam_fan.filter(id__in=sks_lulus_ids)
    sks_belum_lulus = sks_dalam_fan.exclude(id__in=sks_lulus_ids)
    konteks = { 'santri': santri, 'fan': fan, 'sks_lulus': sks_lulus, 'sks_belum_lulus': sks_belum_lulus, 'page_title': f'Detail SKS {fan.nama_fan} - {santri.nama_lengkap}'}
    return render(request, 'core/detail_fan_santri.html', konteks)

# ==============================================================================
# FUNGSI 5: HALAMAN LEADERBOARD PER FAN
# ==============================================================================
def leaderboard_fan_view(request, fan_pk):
    fan = get_object_or_404(Fan, pk=fan_pk)
    peringkat_santri = Santri.objects.filter(status='Aktif').annotate(
        jumlah_lulus_di_fan=Count('riwayat_tes__sks', distinct=True, filter=Q(riwayat_tes__sks__fan=fan) & Q(riwayat_tes__nilai__gte=F('riwayat_tes__sks__nilai_minimal')))
    ).filter(jumlah_lulus_di_fan__gt=0).order_by('-jumlah_lulus_di_fan', 'id')[:5]
    konteks = { 'fan': fan, 'peringkat_santri': peringkat_santri, 'page_title': f'Peringkat Teratas - {fan.nama_fan}'}
    return render(request, 'core/leaderboard_fan.html', konteks)



# ==============================================================================
# FUNGSI 6: HALAMAN LAPORAN DENGAN GRAFIK
# ==============================================================================
# Ganti fungsi laporan_akademik yang lama dengan yang ini

# Ganti fungsi laporan_akademik yang lama dengan versi upgrade ini

# Versi perbaikan untuk bagian awal fungsi laporan_akademik
def laporan_akademik(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Konversi string ke date, jika gagal atau kosong, gunakan default
    try:
        start_date = date.fromisoformat(start_date_str)
    except (ValueError, TypeError):
        # Default: 90 hari yang lalu
        start_date = date.today() - timedelta(days=90)

    try:
        end_date = date.fromisoformat(end_date_str)
    except (ValueError, TypeError):
        # Default: hari ini
        end_date = date.today()
        

# =================================================================
    # KALKULASI ULANG UNTUK PIE CHART - VERSI FINAL DENGAN LOGIKA ANTI-DUPLIKASI
    # =================================================================
    
    # 1. Siapkan daftar kosong untuk menampung semua 'event' penyelesaian Fan yang valid
    all_completion_events = []
    
    semua_santri = Santri.objects.filter(status='Aktif')
    for santri in semua_santri:
        sks_lulus_ids = santri.get_sks_lulus_ids()
        if not sks_lulus_ids:
            continue

        fan_completion_dates = {}
        for fan in Fan.objects.order_by('urutan'):
            sks_in_fan = SKS.objects.filter(fan=fan)
            if sks_in_fan.exists() and sks_in_fan.filter(id__in=sks_lulus_ids).count() == sks_in_fan.count():
                try:
                    tgl_selesai = RiwayatTes.objects.filter(santri=santri, sks__fan=fan).latest('tanggal_tes').tanggal_tes
                    fan_completion_dates[fan.id] = tgl_selesai
                except RiwayatTes.DoesNotExist:
                    pass
        
        if not fan_completion_dates:
            continue

        # 2. Kumpulkan semua event valid ke dalam daftar 'all_completion_events'
        for fan_id, tgl_selesai in fan_completion_dates.items():
            if not (start_date <= tgl_selesai <= end_date):
                continue

            fan_obj = Fan.objects.get(id=fan_id)
            
            tgl_mulai = None
            if fan_obj.urutan == 1:
                try: tgl_mulai = RiwayatTes.objects.filter(santri=santri).earliest('tanggal_tes').tanggal_tes
                except RiwayatTes.DoesNotExist: pass
            else:
                try:
                    fan_sebelumnya = Fan.objects.get(urutan=fan_obj.urutan - 1)
                    tgl_mulai = fan_completion_dates.get(fan_sebelumnya.id)
                except Fan.DoesNotExist: pass
            
            if tgl_mulai is None:
                continue
            
            # Jika semua data valid, tambahkan event ini ke daftar
            all_completion_events.append({
                'durasi': (tgl_selesai - tgl_mulai).days,
                'target': fan_obj.target_durasi_hari
            })

    # 3. Setelah loop selesai, proses daftar yang sudah terkumpul
    
    # Untuk Bar Chart: Jumlah Fan Selesai adalah total event yang terkumpul
    fan_selesai_dalam_periode = len(all_completion_events)
    
    # Untuk Pie Chart: Hitung dari daftar event
    sesuai_target_count = len([event for event in all_completion_events if event['durasi'] <= event['target']])
    melebihi_target_count = len([event for event in all_completion_events if event['durasi'] > event['target']])


    # =================================================================
    # KALKULASI UNTUK BAR CHART (REKAP TES) - VERSI PERBAIKAN
    # =================================================================
    tes_filtered = RiwayatTes.objects.filter(tanggal_tes__range=[start_date, end_date])
    
    # Menghitung jumlah SANTRI UNIK yang ikut tes di periode ini
    total_santri_ikut_tes = tes_filtered.values('santri_id').distinct().count()
    
    # Menghitung jumlah SANTRI UNIK yang punya setidaknya satu tes LULUS
    santri_lulus = tes_filtered.filter(nilai__gte=F('sks__nilai_minimal')).values('santri_id').distinct().count()
    
    # Menghitung jumlah SANTRI UNIK yang punya setidaknya satu tes GUGUR
    # Perlu dihitung terpisah karena satu santri bisa lulus dan gugur di periode yang sama
    santri_gugur = tes_filtered.filter(nilai__lt=F('sks__nilai_minimal')).values('santri_id').distinct().count()

    # Siapkan data untuk dikirim ke template
    labels_target = ['Sesuai Target', 'Melebihi Target']
    data_target = [sesuai_target_count, melebihi_target_count]
    
    # Ganti label 'Total Tes' menjadi lebih deskriptif
    labels_rekap = ['Santri Ikut Tes', 'Santri Lulus', 'Santri Gugur', 'Fan Selesai']
    data_rekap = [total_santri_ikut_tes, santri_lulus, santri_gugur, fan_selesai_dalam_periode]
    # ---- DEBUG: cetak hasil hitungan sebelum dikirim ke template ----
    logger.debug("Target  – Sesuai: %s | Melebihi: %s", sesuai_target_count, melebihi_target_count)
    logger.debug(
        "Rekap   – Total: %s | Lulus: %s | Gugur: %s | Fan Selesai: %s",
        total_santri_ikut_tes, santri_lulus, santri_gugur, fan_selesai_dalam_periode
    )

     # Siapkan data untuk dikirim ke template
    labels_target = ['Sesuai Target', 'Melebihi Target']
    data_target   = [sesuai_target_count, melebihi_target_count]
    labels_rekap  = ['Total Tes', 'Lulus', 'Gugur', 'Fan Selesai']
    data_rekap    = [total_santri_ikut_tes, santri_lulus, santri_gugur, fan_selesai_dalam_periode]
    konteks = {
        'page_title': 'Laporan Rekapitulasi Tes',
        'labels_target_json': json.dumps(labels_target),
        'data_target_json': json.dumps(data_target),
        'labels_rekap_json': json.dumps(labels_rekap),
        'data_rekap_json': json.dumps(data_rekap),
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
    }
    return render(request, 'core/laporan_akademik.html', konteks)
# ==============================================================================
# FUNGSI 7 & 8: HALAMAN STATIS KURIKULUM & DAFTAR SKS
# ==============================================================================
def kurikulum_view(request):
    konteks = {'page_title': 'Kurikulum Asrama Takhossus'}
    return render(request, 'core/kurikulum.html', konteks)

def daftar_sks_view(request):
    semua_sks = SKS.objects.select_related('fan').order_by('fan__urutan', 'nama_sks')
    konteks = { 'page_title': 'Daftar SKS Kurikulum', 'semua_sks': semua_sks }
    return render(request, 'core/daftar_sks.html', konteks)
# Ganti fungsi laporan_rekap_detail yang lama dengan ini
# ==============================================================================
# GANTI FUNGSI LAMA ANDA DENGAN VERSI LENGKAP DAN BERSIH DI BAWAH INI
# ==============================================================================
def laporan_rekap_detail(request):
    # 1. Ambil semua parameter dari URL
    category = request.GET.get('category', '')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # 2. Siapkan variabel awal
    santri_list = Santri.objects.none() # Default: QuerySet kosong
    page_title = f'Detail Kategori: {category.replace("_", " ").title()}'

    # 3. Blok utama untuk memproses data HANYA jika tanggal valid
    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)

        tes_dalam_periode = RiwayatTes.objects.filter(tanggal_tes__range=[start_date, end_date])

        # ==========================================================
        # LOGIKA UNTUK KATEGORI DARI BAR CHART (Total Tes, Lulus, Gugur)
        # ==========================================================
        if category == 'Total Tes':
            santri_ids = tes_dalam_periode.values_list('santri_id', flat=True).distinct()
            santri_list = Santri.objects.filter(id__in=santri_ids)

        elif category == 'Lulus':
            santri_ids = tes_dalam_periode.filter(nilai__gte=F('sks__nilai_minimal')).values_list('santri_id', flat=True).distinct()
            santri_list = Santri.objects.filter(id__in=santri_ids)
            
        elif category == 'Gugur':
            santri_ids = tes_dalam_periode.filter(nilai__lt=F('sks__nilai_minimal')).values_list('santri_id', flat=True).distinct()
            santri_list = Santri.objects.filter(id__in=santri_ids)
        
        # ==========================================================
        # LOGIKA UNTUK KATEGORI 'FAN SELESAI'
        # ==========================================================
        elif category == 'Fan Selesai':
            santri_fan_selesai_ids = set()
            santri_aktif_di_periode = Santri.objects.filter(status='Aktif', id__in=tes_dalam_periode.values_list('santri_id', flat=True).distinct())
            
            for santri in santri_aktif_di_periode:
                sks_lulus_ids = santri.get_sks_lulus_ids()
                if not sks_lulus_ids: continue
                
                for fan in Fan.objects.all():
                    sks_in_fan = SKS.objects.filter(fan=fan)
                    if sks_in_fan.exists() and sks_in_fan.filter(id__in=sks_lulus_ids).count() == sks_in_fan.count():
                        try:
                            tanggal_selesai = RiwayatTes.objects.filter(santri=santri, sks__fan=fan).latest('tanggal_tes').tanggal_tes
                            if start_date <= tanggal_selesai <= end_date:
                                santri_fan_selesai_ids.add(santri.id)
                        except RiwayatTes.DoesNotExist: pass
            santri_list = Santri.objects.filter(id__in=list(santri_fan_selesai_ids))
        
        # ==========================================================
        # LOGIKA UNTUK KATEGORI DARI PIE CHART (Sesuai/Melebihi Target)
        # ==========================================================
        elif category in ['Sesuai Target', 'Melebihi Target']:
            # Ganti dari menyimpan ID menjadi menyimpan detail lengkap
            detail_list = []
            santri_aktif = Santri.objects.filter(status='Aktif')

            for santri in santri_aktif:
                # ... (kode untuk get_sks_lulus_ids dan fan_completion_dates tetap sama) ...
                sks_lulus_ids = santri.get_sks_lulus_ids()
                if not sks_lulus_ids: continue

                fan_completion_dates = {}
                for fan in Fan.objects.order_by('urutan'):
                    sks_in_fan = SKS.objects.filter(fan=fan)
                    if sks_in_fan.exists() and sks_in_fan.filter(id__in=sks_lulus_ids).count() == sks_in_fan.count():
                        try:
                            tgl_selesai = RiwayatTes.objects.filter(santri=santri, sks__fan=fan).latest('tanggal_tes').tanggal_tes
                            fan_completion_dates[fan.id] = tgl_selesai
                        except RiwayatTes.DoesNotExist: pass
                
                if not fan_completion_dates: continue

                for fan_id, tgl_selesai in fan_completion_dates.items():
                    if not (start_date <= tgl_selesai <= end_date): continue

                    fan_obj = Fan.objects.get(id=fan_id)
                    tgl_mulai = None
                    if fan_obj.urutan == 1:
                        try: tgl_mulai = RiwayatTes.objects.filter(santri=santri).earliest('tanggal_tes').tanggal_tes
                        except RiwayatTes.DoesNotExist: pass
                    else:
                        try:
                            fan_sebelumnya = Fan.objects.get(urutan=fan_obj.urutan - 1)
                            tgl_mulai = fan_completion_dates.get(fan_sebelumnya.id)
                        except Fan.DoesNotExist: pass
                    
                    if tgl_mulai is None: continue

                    selisih_hari = (tgl_selesai - tgl_mulai).days
                    status_santri = "Sesuai Target" if selisih_hari <= fan_obj.target_durasi_hari else "Melebihi Target"

                    if status_santri == category:
                        # ===== PERUBAHAN UTAMA DI SINI =====
                        # Kita simpan semua data yang relevan ke dalam sebuah dictionary
                        detail_list.append({
                            'santri': santri,
                            'fan': fan_obj,
                            'tanggal_mulai': tgl_mulai,
                            'tanggal_selesai': tgl_selesai,
                            'durasi': selisih_hari,
                        })
                        # Kita tidak break, agar jika satu santri melebihi target di >1 Fan, semuanya tercatat
            
            # Kirim 'detail_list' ke konteks, bukan 'santri_list' lagi untuk kategori ini
            # Jadi, kita tidak perlu baris `santri_list = Santri.objects.filter(...)` lagi

            for santri in santri_aktif:
                sks_lulus_ids = santri.get_sks_lulus_ids()
                if not sks_lulus_ids: continue

                fan_completion_dates = {}
                for fan in Fan.objects.order_by('urutan'):
                    sks_in_fan = SKS.objects.filter(fan=fan)
                    if sks_in_fan.exists() and sks_in_fan.filter(id__in=sks_lulus_ids).count() == sks_in_fan.count():
                        try:
                            tgl_selesai = RiwayatTes.objects.filter(santri=santri, sks__fan=fan).latest('tanggal_tes').tanggal_tes
                            fan_completion_dates[fan.id] = tgl_selesai
                        except RiwayatTes.DoesNotExist: pass
                
                if not fan_completion_dates: continue

                for fan_id, tgl_selesai in fan_completion_dates.items():
                    if not (start_date <= tgl_selesai <= end_date): continue

                    fan_obj = Fan.objects.get(id=fan_id)
                    tgl_mulai = None
                    if fan_obj.urutan == 1:
                        try: tgl_mulai = RiwayatTes.objects.filter(santri=santri).earliest('tanggal_tes').tanggal_tes
                        except RiwayatTes.DoesNotExist: pass
                    else:
                        try:
                            fan_sebelumnya = Fan.objects.get(urutan=fan_obj.urutan - 1)
                            tgl_mulai = fan_completion_dates.get(fan_sebelumnya.id)
                        except Fan.DoesNotExist: pass
                    
                    if tgl_mulai is None: continue

                    selisih_hari = (tgl_selesai - tgl_mulai).days
                    status_santri = "Sesuai Target" if selisih_hari <= fan_obj.target_durasi_hari else "Melebihi Target"

    except (ValueError, TypeError):
        pass # Jika format tanggal salah, biarkan santri_list kosong
    
    # 4. Kirim data ke template
   # Ubah cara kita membuat konteks agar lebih fleksibel
    konteks = {
        'page_title': page_title,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'category': category,
    }

    if category in ['Sesuai Target', 'Melebihi Target']:
        konteks['rekap_detail_list'] = detail_list # Menggunakan variabel baru dari blok di atas
    else:
        konteks['santri_list'] = santri_list.order_by('nama_lengkap')
    return render(request, 'core/laporan_rekap_detail.html', konteks)