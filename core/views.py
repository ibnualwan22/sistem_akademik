# core/views.py - VERSI LENGKAP DAN FINAL

import base64
import json
import logging
from io import BytesIO
from datetime import date, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

# Impor Django
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q, F, Max
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Impor dari Aplikasi Lokal
from .models import Asrama,Santri, RiwayatTes, SKS, Fan, Pengurus,GrupKontak, KontakPerson
from functools import wraps

# Konfigurasi untuk Matplotlib di server non-GUI
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

# ==============================================================================
# "PENJAGA" ABAC (DECORATOR)
# ==============================================================================
def asrama_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'asrama_id' not in request.session:
            messages.error(request, 'Sesi asrama tidak ditemukan. Silakan login kembali.')
            return redirect('asrama_login')
        try:
            request.asrama = Asrama.objects.get(id=request.session['asrama_id'])
        except Asrama.DoesNotExist:
            del request.session['asrama_id']
            messages.error(request, 'Asrama tidak lagi valid. Silakan login kembali.')
            return redirect('asrama_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# ==============================================================================
# LOGIKA GERBANG AKSES (LOGIN/LOGOUT)
# ==============================================================================
# core/views.py

def asrama_login_view(request):
    """
    [VERSI BARU] View ini hanya menggunakan username dan password.
    Asrama ditentukan dari profil pengguna yang berhasil login.
    """
    if request.user.is_authenticated and 'asrama_id' in request.session:
        return redirect('core:daftar_santri')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 1. Autentikasi pengguna seperti biasa
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            try:
                # 2. Ambil atribut 'asrama' dari profil pengguna
                asrama_pengguna = user.profile.asrama

                if asrama_pengguna and asrama_pengguna.is_active:
                    # 3. Jika berhasil, login dan simpan sesi asrama
                    login(request, user)
                    request.session['asrama_id'] = asrama_pengguna.id
                    request.session['asrama_nama'] = asrama_pengguna.nama_asrama
                    request.session['asrama_logo_url'] = asrama_pengguna.logo.url if asrama_pengguna.logo else None
                    request.session['asrama_kata_pengantar'] = asrama_pengguna.kata_pengantar
                    request.session['asrama_link_instagram'] = asrama_pengguna.link_instagram
                    request.session['asrama_link_youtube'] = asrama_pengguna.link_youtube
                    request.session['asrama_link_whatsapp'] = asrama_pengguna.link_whatsapp
                    request.session['asrama_link_tiktok'] = asrama_pengguna.link_tiktok
                    return redirect('core:daftar_santri')
                else:
                    # Kasus jika profil ada, tapi asrama tidak ada atau tidak aktif
                    messages.error(request, 'Akun Anda tidak terhubung ke asrama yang valid atau aktif.')

            except user._meta.model.profile.RelatedObjectDoesNotExist:
                # Kasus jika pengguna ada TAPI admin belum membuatkan UserProfile untuknya
                messages.error(request, 'Profil untuk akun ini tidak ditemukan. Hubungi administrator.')

        else:
            messages.error(request, 'Username atau Password salah.')

        return redirect('asrama_login')

    return render(request, 'core/asrama_login.html')

def asrama_logout_view(request):
    logout(request)
    messages.success(request, 'Anda telah berhasil logout.')
    return redirect('asrama_login')


# ==============================================================================
# VIEWS UTAMA DENGAN FILTER ABAC
# ==============================================================================

@asrama_required
def daftar_santri(request):
    asrama = request.asrama
    
    # [FIXED] Filter semua query berdasarkan asrama
    semua_kontak = KontakPerson.objects.filter(asrama=asrama).select_related('grup')
    kontak_grup = {}
    for kontak in semua_kontak:
        if kontak.grup.nama_grup not in kontak_grup:
            kontak_grup[kontak.grup.nama_grup] = []
        kontak_grup[kontak.grup.nama_grup].append(kontak)
        
    total_santri_aktif = Santri.objects.filter(asrama=asrama, status='Aktif').count()
    total_pengurus = Pengurus.objects.filter(asrama=asrama).count()
    total_sks = SKS.objects.filter(asrama=asrama).count()
    semua_fan = Fan.objects.filter(asrama=asrama).order_by('urutan')
    
    santri_per_fan_pool = {fan.id: [] for fan in semua_fan}
    # [FIXED] Filter santri berdasarkan asrama
    for santri in Santri.objects.filter(asrama=asrama, status='Aktif'):
        sks_lulus_ids = santri.get_sks_lulus_ids()
        fan_saat_ini_santri = None
        for fan in semua_fan:
            sks_dalam_fan = SKS.objects.filter(asrama=asrama, fan=fan)
            if sks_dalam_fan.exists() and sks_dalam_fan.filter(id__in=sks_lulus_ids).count() < sks_dalam_fan.count():
                fan_saat_ini_santri = fan
                break
        if fan_saat_ini_santri:
            santri_per_fan_pool[fan_saat_ini_santri.id].append(santri.id)

    juara_per_fan = []
    for fan in semua_fan:
        pool_santri_ids = santri_per_fan_pool.get(fan.id, [])
        if not pool_santri_ids:
            continue
        
        peringkat_fan = Santri.objects.filter(asrama=asrama, id__in=pool_santri_ids).annotate(
            jumlah_lulus_di_fan=Count(
                'riwayat_tes__sks',
                distinct=True,
                filter=Q(riwayat_tes__sks__fan=fan) & Q(riwayat_tes__nilai__gte=F('riwayat_tes__sks__nilai_minimal')) & Q(riwayat_tes__status_tes='Selesai')
            )
        ).order_by('-jumlah_lulus_di_fan', 'nama_lengkap')
        
        juara = peringkat_fan.first()
        if juara and juara.jumlah_lulus_di_fan > 0:
            juara_per_fan.append({'fan': fan, 'santri': juara, 'jumlah_lulus': juara.jumlah_lulus_di_fan})
    
    today = date.today()
    aktivitas_terkini = RiwayatTes.objects.filter(asrama=asrama, tanggal_pelaksanaan=today, status_tes='Selesai').order_by('-id')[:5]

    offset_to_last_thursday = (today.weekday() - 3) % 7
    kamis_pekan_ini = today - timedelta(days=offset_to_last_thursday)
    sabtu_awal_pekan = kamis_pekan_ini - timedelta(days=5)
    mvp_santri = Santri.objects.filter(
        asrama=asrama,
        status='Aktif',
        riwayat_tes__tanggal_pelaksanaan__range=[sabtu_awal_pekan, kamis_pekan_ini],
        riwayat_tes__nilai__gte=F('riwayat_tes__sks__nilai_minimal'),
        riwayat_tes__status_tes='Selesai'
    ).annotate(
        lulus_mingguan=Count('riwayat_tes__id'),
        tanggal_lulus_terakhir=Max('riwayat_tes__tanggal_pelaksanaan')
    ).order_by('-lulus_mingguan', 'tanggal_lulus_terakhir').first()

    konteks = {
        'asrama_nama': asrama.nama_asrama,
        'kontak_grup': kontak_grup,
        'page_title': f'Dashboard - {asrama.nama_asrama}',
        'total_santri_aktif': total_santri_aktif,
        'total_pengurus': total_pengurus,
        'total_sks': total_sks,
        'aktivitas_terkini': aktivitas_terkini,
        'juara_per_fan': juara_per_fan,
        'mvp_santri': mvp_santri,
        'periode_mvp_start': sabtu_awal_pekan,
        'periode_mvp_end': kamis_pekan_ini,
    }
    return render(request, 'core/daftar_santri.html', konteks)
# ==============================================================================
# FUNGSI-FUNGSI LAIN YANG MUNGKIN HILANG
# ==============================================================================
@asrama_required
def semua_santri_view(request):
    asrama = request.asrama
    query = request.GET.get('q', '')
    
    # [FIXED] Filter berdasarkan asrama terlebih dahulu
    base_queryset = Santri.objects.filter(asrama=asrama)
    if query:
        base_queryset = base_queryset.filter(nama_lengkap__icontains=query)
    santri_aktif_list = base_queryset.filter(status='Aktif').order_by('nama_lengkap')
    santri_lulus_list = base_queryset.filter(status='Pengurus').order_by('nama_lengkap')
    santri_nonaktif_list = base_queryset.filter(status='Non-Aktif').order_by('nama_lengkap')
    
    konteks = {
        'asrama_nama': asrama.nama_asrama,
        'page_title': 'Daftar Lengkap Santri',
        'santri_aktif_list': base_queryset.filter(status='Aktif').order_by('nama_lengkap'),
        'santri_lulus_list': base_queryset.filter(status='Pengurus').order_by('nama_lengkap'),
        'santri_nonaktif_list': base_queryset.filter(status='Non-Aktif').order_by('nama_lengkap'),
    }
    return render(request, 'core/semua_santri.html', konteks)

@asrama_required
def detail_santri(request, pk):
    asrama = request.asrama
    # [FIXED & SECURE] Filter berdasarkan PK dan Asrama
    santri = get_object_or_404(Santri, pk=pk, asrama=asrama)
    semua_fan = Fan.objects.filter(asrama=asrama).order_by('urutan')
    sks_lulus_ids = santri.get_sks_lulus_ids()
    semua_tes_santri = santri.riwayat_tes.select_related('sks__fan').all()
    fan_completion_dates = santri.get_completed_fans_with_dates()
    
    progress_per_fan = []
    for fan in semua_fan:
        sks_dalam_fan = SKS.objects.filter(fan=fan)
        total_sks_di_fan = sks_dalam_fan.count()
        sks_lulus_di_fan = sks_dalam_fan.filter(id__in=sks_lulus_ids)
        jumlah_lulus_di_fan = sks_lulus_di_fan.count()
        sks_belum_lulus_di_fan = sks_dalam_fan.exclude(id__in=sks_lulus_ids)
        persentase = round((jumlah_lulus_di_fan / total_sks_di_fan) * 100) if total_sks_di_fan > 0 else 0
        
        # Logika durasi di sini berbeda dengan di laporan, ini berdasarkan fan sebelumnya.
        tanggal_selesai = fan_completion_dates.get(fan)
        tanggal_mulai = None
        if fan.urutan == 1:
            if semua_tes_santri.exists():
                tanggal_mulai = semua_tes_santri.earliest('tanggal_pelaksanaan').tanggal_pelaksanaan
        else:
            try:
                fan_sebelumnya = Fan.objects.get(urutan=fan.urutan - 1)
                tanggal_mulai = fan_completion_dates.get(fan_sebelumnya)
            except Fan.DoesNotExist: pass

        durasi_studi = None
        status_target = None
        if tanggal_mulai and tanggal_selesai:
            selisih_hari_int = (tanggal_selesai - tanggal_mulai).days
            durasi_studi = f"{selisih_hari_int // 30} bulan, {selisih_hari_int % 30} hari" if selisih_hari_int >= 30 else f"{selisih_hari_int if selisih_hari_int >= 0 else 0} hari"
            if fan.target_durasi_hari > 0 and selisih_hari_int is not None:
                status_target = "Sesuai Target" if selisih_hari_int <= fan.target_durasi_hari else "Melebihi Target"
        
        progress_per_fan.append({
            'fan': fan, 'total_sks': total_sks_di_fan, 'jumlah_lulus': jumlah_lulus_di_fan,
            'persentase': persentase, 'durasi_studi': durasi_studi, 'status_target': status_target,
            'sks_lulus': sks_lulus_di_fan, 'sks_belum_lulus': sks_belum_lulus_di_fan
        })

    fan_saat_ini_obj = next((data['fan'] for data in progress_per_fan if data['persentase'] < 100), None)
    
    if not fan_saat_ini_obj and progress_per_fan:
        total_durasi_teks = "N/A"
        if fan_completion_dates and semua_tes_santri.exists():
            tanggal_paling_akhir = max(fan_completion_dates.values())
            tanggal_paling_awal = semua_tes_santri.earliest('tanggal_pelaksanaan').tanggal_pelaksanaan
            total_durasi_hari = (tanggal_paling_akhir - tanggal_paling_awal).days
            total_durasi_teks = f"{total_durasi_hari // 30} bulan, {total_durasi_hari % 30} hari" if total_durasi_hari >= 30 else f"{total_durasi_hari} hari"
        fan_saat_ini = f"Selamat! Anda telah menyelesaikan Program Takhossus dengan total durasi {total_durasi_teks}"
    else:
        fan_saat_ini = fan_saat_ini_obj
        
    konteks = {
        'page_title': f'Profil {santri.nama_lengkap}',
        'asrama_nama': asrama.nama_asrama,
        'santri': santri,
        'progress_per_fan': progress_per_fan,
        'semua_tes': semua_tes_santri.order_by('-tanggal_pelaksanaan'),
        'fan_saat_ini': fan_saat_ini,
    }
    return render(request, 'core/detail_santri.html', konteks)

@asrama_required
def detail_fan_santri(request, santri_pk, fan_pk):
    asrama = request.asrama
    santri = get_object_or_404(Santri, pk=santri_pk, asrama=asrama)
    fan = get_object_or_404(Fan, pk=fan_pk, asrama=asrama)
    sks_lulus_ids = santri.get_sks_lulus_ids()
    sks_dalam_fan = SKS.objects.filter(fan=fan)
    sks_lulus = sks_dalam_fan.filter(id__in=sks_lulus_ids)
    sks_belum_lulus = sks_dalam_fan.exclude(id__in=sks_lulus_ids)
    konteks = { 'santri': santri, 'fan': fan, 'sks_lulus': sks_lulus, 'sks_belum_lulus': sks_belum_lulus, 'page_title': f'Detail SKS {fan.nama_fan} - {santri.nama_lengkap}'}
    return render(request, 'core/detail_fan_santri.html', konteks)

@asrama_required
def leaderboard_fan_view(request, fan_pk):
    asrama = request.asrama
    # [FIXED & SECURE]
    fan = get_object_or_404(Fan, pk=fan_pk, asrama=asrama)
    peringkat_santri = Santri.objects.filter(asrama=asrama, status='Aktif').annotate(
        jumlah_lulus_di_fan=Count('riwayat_tes__sks', distinct=True, filter=Q(riwayat_tes__sks__fan=fan) & Q(riwayat_tes__nilai__gte=F('riwayat_tes__sks__nilai_minimal')))
    ).filter(jumlah_lulus_di_fan__gt=0).order_by('-jumlah_lulus_di_fan', 'id')[:5]
    konteks = { 'fan': fan, 'peringkat_santri': peringkat_santri, 'page_title': f'Peringkat Teratas - {fan.nama_fan}'}
    return render(request, 'core/leaderboard_fan.html', konteks)

@asrama_required
def kurikulum_view(request):
    asrama = request.asrama
    konteks = {'page_title': f'Kurikulum Asrama { asrama.nama_asrama }',}
    return render(request, 'core/kurikulum.html', konteks)

@asrama_required
def daftar_sks_view(request):
    asrama = request.asrama
    # [FIXED]
    semua_sks = SKS.objects.filter(asrama=asrama).select_related('fan').order_by('fan__urutan', 'nama_sks')
    konteks = { 'page_title': f'Daftar SKS Kurikulum { asrama.nama_asrama }', 'semua_sks': semua_sks }
    return render(request, 'core/daftar_sks.html', konteks)

@asrama_required
def laporan_akademik(request):
    asrama = request.asrama
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_fan_id = request.GET.get('fan_id')

    try:
        start_date = date.fromisoformat(start_date_str) if start_date_str else date.today() - timedelta(days=90)
        end_date = date.fromisoformat(end_date_str) if end_date_str else date.today()
    except (ValueError, TypeError):
        end_date = date.today()
        start_date = end_date - timedelta(days=90)

    # Query dasar tes yang relevan
    tes_selesai_query = RiwayatTes.objects.filter(
        asrama=asrama,
        tanggal_pelaksanaan__range=[start_date, end_date],
        status_tes='Selesai'
    )
    # Ambil santri yang relevan
    santri_query = Santri.objects.filter(asrama=asrama, riwayat_tes__in=tes_selesai_query).distinct()
    
    if selected_fan_id and selected_fan_id.isdigit():
        santri_query = santri_query.filter(riwayat_tes__sks__fan_id=selected_fan_id).distinct()
        tes_selesai_query = tes_selesai_query.filter(sks__fan_id=selected_fan_id)

    sesuai_target_count, melebihi_target_count, fan_selesai_dalam_periode = 0, 0, 0

    for santri in santri_query:
        completed_fans = santri.get_completed_fans_with_dates()
        for fan, tgl_selesai in completed_fans.items():
            if selected_fan_id and selected_fan_id.isdigit() and str(fan.id) != selected_fan_id:
                continue
            if start_date <= tgl_selesai <= end_date:
                fan_selesai_dalam_periode += 1
                try:
                    # KUNCI PERBAIKAN: Ambil SEMUA tes untuk menemukan tgl_mulai yang akurat
                    semua_tes_fan = RiwayatTes.objects.filter(santri=santri, sks__fan=fan)
                    tgl_mulai = semua_tes_fan.earliest('tanggal_pelaksanaan').tanggal_pelaksanaan
                    durasi = (tgl_selesai - tgl_mulai).days
                    if durasi <= fan.target_durasi_hari:
                        sesuai_target_count += 1
                    else:
                        melebihi_target_count += 1
                except RiwayatTes.DoesNotExist:
                    pass
    
    total_tes = tes_selesai_query.count()
    jumlah_lulus = tes_selesai_query.filter(nilai__gte=F('sks__nilai_minimal')).count()
    jumlah_gugur = total_tes - jumlah_lulus

    konteks = {
        'asrama_nama': asrama.nama_asrama,
        'page_title': 'Laporan Rekapitulasi Tes',
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'all_fans': Fan.objects.filter(asrama=asrama).order_by('urutan'),
        'selected_fan_id': selected_fan_id,
        'labels_target_json': json.dumps(['Sesuai Target', 'Melebihi Target']),
        'data_target_json': json.dumps([sesuai_target_count, melebihi_target_count]),
        'labels_rekap_json': json.dumps(['Total Tes', 'Lulus', 'Gugur', 'Fan Selesai']),
        'data_rekap_json': json.dumps([total_tes, jumlah_lulus, jumlah_gugur, fan_selesai_dalam_periode]),
    }
    return render(request, 'core/laporan_akademik.html', konteks)



# GANTI FUNGSI INI DENGAN VERSI BARU YANG JUGA LEBIH BERSIH
def laporan_rekap_detail(request):
    # ... (bagian mengambil filter tetap sama) ...
    category = request.GET.get('category', '')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_fan_id = request.GET.get('fan_id')

    # ... (bagian inisialisasi konteks tetap sama) ...
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

        # Tentukan santri yang relevan berdasarkan filter
        tes_filtered = RiwayatTes.objects.filter(tanggal_pelaksanaan__range=[start_date, end_date])
        if selected_fan_id and selected_fan_id.isdigit():
            tes_filtered = tes_filtered.filter(sks__fan_id=selected_fan_id)
        
        relevant_santri_ids = tes_filtered.values_list('santri_id', flat=True).distinct()
        semua_santri = Santri.objects.filter(id__in=relevant_santri_ids)
        
        # --- LOGIKA BARU YANG LEBIH SEDERHANA & KONSISTEN ---
        # A. Logika untuk kategori dari PIE CHART dan 'Fan Selesai'
        if category in ['Sesuai Target', 'Melebihi Target', 'Fan Selesai']:
            for santri in semua_santri:
                # Panggil method baru dari model
                completed_fans = santri.get_completed_fans_with_dates()
                for fan, tgl_selesai in completed_fans.items():
                    # Cek apakah fan ini sesuai dengan filter (jika ada)
                    if selected_fan_id and selected_fan_id.isdigit() and fan.id != int(selected_fan_id):
                        continue
                    
                    if not (start_date <= tgl_selesai <= end_date): continue

                    keterangan = 'Menyelesaikan Fan'
                    if category != 'Fan Selesai':
                        try:
                            tes_dalam_fan = RiwayatTes.objects.filter(santri=santri, sks__fan=fan)
                            tgl_mulai = tes_dalam_fan.earliest('tanggal_pelaksanaan').tanggal_pelaksanaan
                            durasi = (tgl_selesai - tgl_mulai).days
                            status_santri = "Sesuai Target" if durasi <= fan.target_durasi_hari else "Melebihi Target"
                            if status_santri != category: continue # Lewati jika tidak cocok kategori
                            keterangan = f"Selesai Fan ({category})"
                        except RiwayatTes.DoesNotExist: continue
                    
                    unified_list.append({
                        'santri': santri,
                        'tanggal_event': tgl_selesai,
                        'keterangan': keterangan,
                        'detail_objek': fan.nama_fan
                    })
        
        # B. Logika untuk Lulus, Gugur, Ikut Tes
        else:
            # ... (logika ini sudah benar, hanya perlu menyesuaikan 'tes_filtered') ...
            relevant_tests = RiwayatTes.objects.none()
            if category == 'Santri Ikut Tes' or category == 'Total Tes':
                relevant_tests = tes_filtered
            elif category == 'Santri Lulus' or category == 'Lulus':
                relevant_tests = tes_filtered.filter(nilai__gte=F('sks__nilai_minimal'))
            elif category == 'Santri Gugur' or category == 'Gugur':
                relevant_tests = tes_filtered.filter(nilai__lt=F('sks__nilai_minimal'))
            for tes in relevant_tests.select_related('santri', 'sks', 'sks__fan'):
                unified_list.append({
                    'santri': tes.santri,
                    'tanggal_event': tes.tanggal_pelaksanaan,
                    'keterangan': f"{tes.status_kelulusan} Tes",
                    'detail_objek': tes.sks.nama_sks
                })
        
        konteks['unified_list'] = sorted(unified_list, key=lambda x: x['tanggal_event'], reverse=True)

    except (ValueError, TypeError):
        pass
    
    return render(request, 'core/laporan_rekap_detail.html', konteks)

# core/views.py

# core/views.py

@asrama_required
def riwayat_tes_view(request):
    asrama = request.asrama
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_fan_id = request.GET.get('fan_id')
    selected_status = request.GET.get('status_tes')

    try:
        start_date = date.fromisoformat(start_date_str) if start_date_str else date.today() - timedelta(days=365)
        end_date = date.fromisoformat(end_date_str) if end_date_str else date.today()
    except (ValueError, TypeError):
        end_date = date.today()
        start_date = end_date - timedelta(days=365)

    riwayat_list = RiwayatTes.objects.filter(asrama=asrama, tanggal_pelaksanaan__range=[start_date, end_date])
    if selected_fan_id and selected_fan_id.isdigit():
        riwayat_list = riwayat_list.filter(sks__fan_id=selected_fan_id)

    if selected_status:
        riwayat_list = riwayat_list.filter(status_tes=selected_status)
    else:
        # Jika tidak ada filter status, defaultnya tampilkan 'Selesai'
        riwayat_list = riwayat_list.filter(status_tes='Selesai')
        selected_status = 'Selesai'

    konteks = {
        'page_title': f'Riwayat Tes Santri { asrama.nama_asrama }',
        # PENTING: .distinct() untuk mencegah duplikasi data
        'riwayat_list': riwayat_list.order_by('-tanggal_pelaksanaan', '-id').distinct(),
        'all_fans': Fan.objects.filter(asrama=asrama).order_by('urutan'),
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'selected_fan_id': selected_fan_id,
        'selected_status': selected_status,
    }
    return render(request, 'core/riwayat_tes.html', konteks)

# Tambahkan dua fungsi ini di views.py

@asrama_required
def daftar_pengurus_view(request):
    asrama = request.asrama
    # [FIXED]
    semua_pengurus = Pengurus.objects.filter(asrama=asrama).order_by('nama_lengkap')
    konteks = {
        'page_title': f'Struktur Kepengurusan { asrama.nama_asrama }',
        'semua_pengurus': semua_pengurus
    }
    return render(request, 'core/daftar_pengurus.html', konteks)

@asrama_required
def detail_pengurus_view(request, pk):
    asrama = request.asrama
    # [FIXED & SECURE]
    pengurus = get_object_or_404(Pengurus, pk=pk, asrama=asrama)
    konteks = {
        'page_title': f'Profil Pengurus: {pengurus.nama_lengkap}',
        'pengurus': pengurus
    }
    return render(request, 'core/detail_pengurus.html', konteks)

# core/views.py
@asrama_required
def export_tes_excel(request):
    asrama = request.asrama
    """
    Mengekspor data Riwayat Tes yang sudah difilter ke dalam format file Excel (.xlsx).
    """
    # 1. AMBIL DATA DENGAN LOGIKA FILTER YANG SAMA PERSIS DENGAN `riwayat_tes_view`
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_fan_id = request.GET.get('fan_id')
    selected_status = request.GET.get('status_tes')

    try:
        start_date = date.fromisoformat(start_date_str) if start_date_str else date.today() - timedelta(days=365)
        end_date = date.fromisoformat(end_date_str) if end_date_str else date.today()
    except (ValueError, TypeError):
        end_date = date.today(); start_date = end_date - timedelta(days=365)

    riwayat_list = RiwayatTes.objects.select_related('santri', 'sks', 'sks__fan', 'penguji').filter(tanggal_pelaksanaan__range=[start_date, end_date])
    if selected_fan_id and selected_fan_id.isdigit():
        riwayat_list = riwayat_list.filter(sks__fan_id=selected_fan_id)
    if selected_status:
        riwayat_list = riwayat_list.filter(status_tes=selected_status)
    else:
        riwayat_list = riwayat_list.filter(status_tes='Selesai')

    riwayat_list = riwayat_list.order_by('tanggal_pelaksanaan', 'santri__nama_lengkap')
    
    # 2. BUAT FILE EXCEL DI MEMORI
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="riwayat_tes_{date.today().isoformat()}.xlsx"'

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Riwayat Tes'

    # Buat Header Tabel
    headers = [
        'Tanggal Pelaksanaan', 'Nama Santri', 'Fan', 'SKS / Kitab', 
        'Penguji', 'Nilai', 'Status Tes', 'Status Kelulusan'
    ]
    worksheet.append(headers)
    
    # Beri style pada Header
    header_font = Font(bold=True)
    for cell in worksheet[1]:
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    # Atur lebar kolom
    worksheet.column_dimensions['A'].width = 20
    worksheet.column_dimensions['B'].width = 30
    worksheet.column_dimensions['C'].width = 20
    worksheet.column_dimensions['D'].width = 30
    worksheet.column_dimensions['E'].width = 30
    worksheet.column_dimensions['F'].width = 10
    worksheet.column_dimensions['G'].width = 15
    worksheet.column_dimensions['H'].width = 15

    # Isi baris data
    for tes in riwayat_list:
        row = [
            tes.tanggal_pelaksanaan,
            tes.santri.nama_lengkap,
            tes.sks.fan.nama_fan,
            tes.sks.nama_sks,
            tes.penguji.nama_lengkap if tes.penguji else '-',
            tes.nilai,
            tes.status_tes,
            tes.status_kelulusan
        ]
        worksheet.append(row)
    
    # Simpan workbook ke response
    workbook.save(response)
    
    return response
def export_laporan_pdf(request):
    """
    Mengekspor laporan PDF dengan logika yang sudah diperbaiki dan konsisten.
    """
    # ======================================================================
    # Bagian 1: Mengambil dan Memproses Filter (Sama persis dengan laporan_akademik)
    # ======================================================================
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_fan_id = request.GET.get('fan_id')

    try:
        start_date = date.fromisoformat(start_date_str) if start_date_str else date.today() - timedelta(days=90)
        end_date = date.fromisoformat(end_date_str) if end_date_str else date.today()
    except (ValueError, TypeError):
        end_date = date.today()
        start_date = end_date - timedelta(days=90)

    # ======================================================================
    # Bagian 2: Menghitung Data Laporan (Sama persis dengan laporan_akademik)
    # ======================================================================

    # --- Data untuk Pie Chart ---
    tes_selesai_query = RiwayatTes.objects.filter(
        tanggal_pelaksanaan__range=[start_date, end_date],
        status_tes='Selesai'
    )
    santri_query = Santri.objects.filter(riwayat_tes__in=tes_selesai_query).distinct()
    
    if selected_fan_id and selected_fan_id.isdigit():
        santri_query = santri_query.filter(riwayat_tes__sks__fan_id=selected_fan_id).distinct()
        tes_selesai_query = tes_selesai_query.filter(sks__fan_id=selected_fan_id)

    santri_selesai_fan = []
    for santri in santri_query:
        completed_fans = santri.get_completed_fans_with_dates()
        for fan, tgl_selesai in completed_fans.items():
            if selected_fan_id and selected_fan_id.isdigit() and str(fan.id) != selected_fan_id:
                continue
            if start_date <= tgl_selesai <= end_date:
                try:
                    semua_tes_fan = RiwayatTes.objects.filter(santri=santri, sks__fan=fan)
                    tgl_mulai = semua_tes_fan.earliest('tanggal_pelaksanaan').tanggal_pelaksanaan
                    durasi = (tgl_selesai - tgl_mulai).days
                    status_target = "Sesuai Target" if durasi <= fan.target_durasi_hari else "Melebihi Target"
                    santri_selesai_fan.append({'santri': santri, 'status': status_target, 'fan': fan})
                except RiwayatTes.DoesNotExist:
                    continue
    
    sesuai_target_list = [d for d in santri_selesai_fan if d['status'] == 'Sesuai Target']
    melebihi_target_list = [d for d in santri_selesai_fan if d['status'] == 'Melebihi Target']
    sesuai_target_count = len(sesuai_target_list)
    melebihi_target_count = len(melebihi_target_list)

    # --- Data untuk Bar Chart ---
    total_tes = tes_selesai_query.count()
    jumlah_lulus = tes_selesai_query.filter(nilai__gte=F('sks__nilai_minimal')).count()
    jumlah_gugur = total_tes - jumlah_lulus

    # ======================================================================
    # Bagian 3: Membuat Gambar Diagram
    # ======================================================================
    
    # Pie Chart
    labels_pie = 'Sesuai Target', 'Melebihi Target'
    sizes_pie = [sesuai_target_count, melebihi_target_count] if sesuai_target_count or melebihi_target_count else [1, 0]
    if not any(sizes_pie): labels_pie = ['Tidak Ada Data']
    
    fig1, ax1 = plt.subplots(figsize=(5, 4))
    ax1.pie(sizes_pie, labels=labels_pie, autopct='%1.1f%%', shadow=True, startangle=140, explode=(0.05, 0))
    ax1.axis('equal')
    
    buf_pie = BytesIO()
    plt.savefig(buf_pie, format='png', bbox_inches='tight', transparent=True)
    pie_chart_base64 = base64.b64encode(buf_pie.getvalue()).decode('utf-8')
    plt.close(fig1)

    # Bar Chart
    labels_bar = ['Total Tes', 'Lulus', 'Gugur']
    values_bar = [total_tes, jumlah_lulus, jumlah_gugur]
    
    fig2, ax2 = plt.subplots(figsize=(5.5, 4.5))
    bars = ax2.bar(labels_bar, values_bar, color=['#5c6bc0', '#66bb6a', '#ef5350'], width=0.6, zorder=2)
    ax2.set_ylabel('Jumlah')
    ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)
    ax2.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.5)
    ax2.set_axisbelow(True)
    ax2.bar_label(bars, padding=3, fontsize=10)
    
    buf_bar = BytesIO()
    plt.savefig(buf_bar, format='png', bbox_inches='tight', transparent=True)
    bar_chart_base64 = base64.b64encode(buf_bar.getvalue()).decode('utf-8')
    plt.close(fig2)

    # ======================================================================
    # Bagian 4: Merender Hasil ke PDF
    # ======================================================================
    konteks = {
        'sesuai_target_list': sesuai_target_list, 
        'melebihi_target_list': melebihi_target_list, 
        'sesuai_target_count': sesuai_target_count, 
        'melebihi_target_count': melebihi_target_count, 
        'total_tes': total_tes, 'jumlah_lulus': jumlah_lulus, 'jumlah_gugur': jumlah_gugur, 
        'pie_chart_base64': pie_chart_base64, 'bar_chart_base64': bar_chart_base64, 
        'start_date': start_date, 'end_date': end_date
    }
    
    html = render_to_string('pdf/laporan_akademik_pdf.html', konteks)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="laporan_akademik_{date.today()}.pdf"'
        return response
    
    return HttpResponse(f"Terjadi kesalahan saat membuat PDF: {pdf.err}", status=500)
# core/views.py

def daftar_kontak_view(request):
    semua_kontak = KontakPerson.objects.all().select_related('grup')
    kontak_grup = {}
    for kontak in semua_kontak:
        if kontak.grup.nama_grup not in kontak_grup:
            kontak_grup[kontak.grup.nama_grup] = []
        kontak_grup[kontak.grup.nama_grup].append(kontak)
        
    konteks = {
        'page_title': 'Contact Person',
        'kontak_grup': kontak_grup,
    }
    return render(request, 'core/daftar_kontak.html', konteks)

@csrf_protect
@never_cache
def admin_login_view(request):
    """
    Custom admin login view dengan desain colorful
    """
    # Redirect jika sudah login
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('/admin/')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            # [PERUBAHAN DI SINI] Ubah 'user.is_staff' menjadi 'user.is_active'
        if user is not None and user.is_active:
            try:
                asrama_pengguna = user.profile.asrama
                
                if asrama_pengguna and asrama_pengguna.is_active:
                    login(request, user)
                    request.session['asrama_id'] = asrama_pengguna.id
                    request.session['asrama_nama'] = asrama_pengguna.nama_asrama
                    return redirect('core:daftar_santri')
                else:
                    messages.error(request, 'Akun Anda tidak terhubung ke asrama yang valid atau aktif.')
            
            except user._meta.model.profile.RelatedObjectDoesNotExist:
                messages.error(request, 'Profil untuk akun ini tidak ditemukan. Hubungi administrator.')

        else:
            messages.error(request, 'Username atau Password salah, atau akun Anda tidak aktif.')

        return redirect('asrama_login')
        
    return render(request, 'core/asrama_login.html')
@login_required
def admin_dashboard(request):
    """
    Dashboard admin setelah login
    """
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak.')
        return redirect('core:admin_login')
    
    context = {
        'user': request.user,
        'title': 'Dashboard Admin',
        'total_users': 0,  # Tambahkan data sesuai kebutuhan
        'total_santri': 0,
        'total_kelas': 0,
    }
    return render(request, 'admin/dashboard.html', context)

def custom_admin_login(request):
    """
    Override default Django admin login
    """
    return admin_login_view(request)
# core/views.py

def asrama_logout_view(request):
    # Hapus sesi dan data login pengguna
    logout(request)

    # Tampilkan halaman konfirmasi logout
    return render(request, 'core/logout_done.html')