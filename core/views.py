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
# GANTI LAGI FUNGSI INI DENGAN VERSI YANG SUDAH MEMFILTER PIE CHART
# ==============================================================================
# GANTI LAGI FUNGSI INI DAN PASTIKAN INDEN-NYA BENAR
# ==============================================================================
# ==============================================================================
# GANTI TOTAL FUNGSI INI DENGAN VERSI FINAL (FIX PIE CHART & FILTER)
# ==============================================================================
def laporan_akademik(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_fan_id = request.GET.get('fan_id')

    try:
        start_date = date.fromisoformat(start_date_str) if start_date_str else date.today() - timedelta(days=90)
        end_date = date.fromisoformat(end_date_str) if end_date_str else date.today()
    except (ValueError, TypeError):
        end_date = date.today()
        start_date = end_date - timedelta(days=90)

    # Filter dasar untuk tes
    tes_filtered = RiwayatTes.objects.filter(tanggal_tes__range=[start_date, end_date])
    if selected_fan_id and selected_fan_id.isdigit():
        tes_filtered = tes_filtered.filter(sks__fan_id=selected_fan_id)

    # --- PERBAIKAN LOGIKA PIE CHART (ANTI DUPLIKASI) ---
    sesuai_target_count = 0
    melebihi_target_count = 0
    fan_selesai_dalam_periode = 0
    
    # Tentukan Fan mana yang akan diperiksa
    fans_to_check = Fan.objects.all()
    if selected_fan_id and selected_fan_id.isdigit():
        fans_to_check = fans_to_check.filter(id=selected_fan_id)

    # Dapatkan santri yang relevan
    relevant_santri_ids = tes_filtered.values_list('santri_id', flat=True).distinct()
    semua_santri = Santri.objects.filter(id__in=relevant_santri_ids)
    
    for santri in semua_santri:
        sks_lulus_ids = santri.get_sks_lulus_ids()
        if not sks_lulus_ids: continue
        
        # Loop hanya pada fan yang sudah difilter
        for fan in fans_to_check.order_by('urutan'):
            sks_in_fan = SKS.objects.filter(fan=fan)
            # Cek apakah fan ini sudah diselesaikan oleh santri
            if sks_in_fan.exists() and sks_in_fan.filter(id__in=sks_lulus_ids).count() == sks_in_fan.count():
                try:
                    tes_dalam_fan = RiwayatTes.objects.filter(santri=santri, sks__fan=fan)
                    tgl_mulai = tes_dalam_fan.earliest('tanggal_tes').tanggal_tes
                    tgl_selesai = tes_dalam_fan.latest('tanggal_tes').tanggal_tes
                    
                    # Hanya proses jika tanggal selesainya masuk dalam periode filter
                    if start_date <= tgl_selesai <= end_date:
                        fan_selesai_dalam_periode += 1 # Tambah untuk Bar Chart
                        durasi = (tgl_selesai - tgl_mulai).days
                        
                        # Tambah untuk Pie Chart
                        if durasi <= fan.target_durasi_hari:
                            sesuai_target_count += 1
                        else:
                            melebihi_target_count += 1
                except RiwayatTes.DoesNotExist:
                    pass

    # --- PERHITUNGAN BAR CHART (TETAP SAMA) ---
    total_tes = tes_filtered.count()
    jumlah_lulus = tes_filtered.filter(nilai__gte=F('sks__nilai_minimal')).count()
    jumlah_gugur = tes_filtered.filter(nilai__lt=F('sks__nilai_minimal')).count()

    # --- KONTEKS (TETAP SAMA) ---
    all_fans = Fan.objects.all().order_by('urutan')
    konteks = {
        'page_title': 'Laporan Rekapitulasi Tes',
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'all_fans': all_fans,
        'selected_fan_id': int(selected_fan_id) if selected_fan_id and selected_fan_id.isdigit() else '',
        'labels_target_json': json.dumps(['Sesuai Target', 'Melebihi Target']),
        'data_target_json': json.dumps([sesuai_target_count, melebihi_target_count]),
        'labels_rekap_json': json.dumps(['Total Tes', 'Lulus', 'Gugur', 'Fan Selesai']),
        'data_rekap_json': json.dumps([total_tes, jumlah_lulus, jumlah_gugur, fan_selesai_dalam_periode]),
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


# ==============================================================================
# GANTI TOTAL FUNGSI INI DI views.py ANDA DENGAN VERSI FINAL DI BAWAH
# ==============================================================================
# ==============================================================================
# GANTI TOTAL FUNGSI INI DAN PASTIKAN INDEN-NYA BENAR
# ==============================================================================
def laporan_rekap_detail(request):
    category = request.GET.get('category', '')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_fan_id = request.GET.get('fan_id')

    konteks = {
        'page_title': f'Detail Kategori: {category.replace("_", " ")}',
        'start_date': start_date_str,
        'end_date': end_date_str,
        'category': category,
        'unified_list': [],
    }

    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
        
        unified_list = []

        base_sks_query = SKS.objects.all()
        if selected_fan_id and selected_fan_id.isdigit():
            base_sks_query = base_sks_query.filter(fan_id=selected_fan_id)

        # A. Logika untuk kategori dari PIE CHART (Capaian Target)
        if category in ['Sesuai Target', 'Melebihi Target']:
            santri_aktif_ids = RiwayatTes.objects.filter(
                tanggal_tes__range=[start_date, end_date],
                sks__in=base_sks_query
            ).values_list('santri_id', flat=True).distinct()
            santri_aktif = Santri.objects.filter(id__in=santri_aktif_ids)
            
            for santri in santri_aktif:
                sks_lulus_ids = santri.get_sks_lulus_ids()
                if not sks_lulus_ids: continue
                
                fans_to_check = Fan.objects.all()
                if selected_fan_id and selected_fan_id.isdigit():
                    fans_to_check = fans_to_check.filter(id=selected_fan_id)

                for fan in fans_to_check.order_by('urutan'):
                    sks_in_fan = SKS.objects.filter(fan=fan)
                    if sks_in_fan.exists() and sks_in_fan.filter(id__in=sks_lulus_ids).count() == sks_in_fan.count():
                        try:
                            tes_dalam_fan = RiwayatTes.objects.filter(santri=santri, sks__fan=fan)
                            tgl_mulai = tes_dalam_fan.earliest('tanggal_tes').tanggal_tes
                            tgl_selesai = tes_dalam_fan.latest('tanggal_tes').tanggal_tes
                            
                            if not (start_date <= tgl_selesai <= end_date): continue

                            durasi = (tgl_selesai - tgl_mulai).days
                            status_santri = "Sesuai Target" if durasi <= fan.target_durasi_hari else "Melebihi Target"
                            
                            if status_santri == category:
                                unified_list.append({
                                    'santri': santri,
                                    'tanggal_event': tgl_selesai,
                                    'keterangan': f"Selesai Fan ({category})",
                                    'detail_objek': fan.nama_fan
                                })
                        except RiwayatTes.DoesNotExist:
                            pass

        # B. Logika untuk 'Fan Selesai'
        elif category == 'Fan Selesai':
            santri_aktif = Santri.objects.filter(status='Aktif', riwayat_tes__sks__in=base_sks_query).distinct()
            for santri in santri_aktif:
                sks_lulus_ids = santri.get_sks_lulus_ids()
                if not sks_lulus_ids: continue
                
                fans_to_check = Fan.objects.all()
                if selected_fan_id and selected_fan_id.isdigit():
                    fans_to_check = fans_to_check.filter(id=selected_fan_id)

                for fan in fans_to_check.order_by('urutan'):
                    sks_in_fan = SKS.objects.filter(fan=fan)
                    if sks_in_fan.exists() and sks_in_fan.filter(id__in=sks_lulus_ids).count() == sks_in_fan.count():
                        try:
                            tanggal_selesai_fan = RiwayatTes.objects.filter(santri=santri, sks__fan=fan).latest('tanggal_tes').tanggal_tes
                            if start_date <= tanggal_selesai_fan <= end_date:
                                unified_list.append({
                                    'santri': santri,
                                    'tanggal_event': tanggal_selesai_fan,
                                    'keterangan': 'Menyelesaikan Fan',
                                    'detail_objek': fan.nama_fan
                                })
                        except RiwayatTes.DoesNotExist:
                            pass

        # C. Logika untuk Lulus, Gugur, Ikut Tes
        else:
            tes_dalam_periode = RiwayatTes.objects.filter(
                tanggal_tes__range=[start_date, end_date],
                sks__in=base_sks_query
            )
            relevant_tests = RiwayatTes.objects.none()
            if category == 'Santri Ikut Tes' or category == 'Total Tes':
                relevant_tests = tes_dalam_periode
            elif category == 'Santri Lulus'or category == 'Lulus':
                relevant_tests = tes_dalam_periode.filter(nilai__gte=F('sks__nilai_minimal'))
            elif category == 'Santri Gugur'or category == 'Gugur':
                relevant_tests = tes_dalam_periode.filter(nilai__lt=F('sks__nilai_minimal'))
            
            for tes in relevant_tests.select_related('santri', 'sks'):
                unified_list.append({
                    'santri': tes.santri,
                    'tanggal_event': tes.tanggal_tes,
                    'keterangan': f"{tes.status_kelulusan} Tes",
                    'detail_objek': tes.sks.nama_sks
                })
        
        konteks['unified_list'] = sorted(unified_list, key=lambda x: x['tanggal_event'], reverse=True)

    except (ValueError, TypeError):
        pass
    
    return render(request, 'core/laporan_rekap_detail.html', konteks)