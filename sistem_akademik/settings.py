# settings.py - VERSI FINAL UNTUK DEPLOYMENT DI RENDER.COM

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# PENGATURAN KUNCI, DEBUG, DAN HOST
# Ini satu-satunya tempat untuk mengatur variabel-variabel ini.
# ==============================================================================

# Ambil Secret Key dari environment variable.
# Ini WAJIB diatur di Render untuk keamanan.
# Ambil Secret Key dari environment variable, beri nilai default untuk lokal.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-ini-hanya-untuk-lokal-dan-tidak-apa-apa')
DB_NAME = os.environ.get('DB_NAME', 'akademik')
# DEBUG=True jika ada env var DEBUG=True, jika tidak maka otomatis False.
# Di Render, JANGAN set variabel DEBUG agar otomatis False (aman).
# DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
DEBUG = True # <-- AKTIFKAN SEMENTARA UNTUK LOKAL
# Konfigurasi ALLOWED_HOSTS untuk Render dan Lokal
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
]

# Ambil nama host yang diberikan otomatis oleh Render.com dan masukkan ke daftar.
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# ==============================================================================
# APLIKASI DAN MIDDLEWARE
# ==============================================================================

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise',
    'django.contrib.staticfiles',

    # Aplikasi kita sendiri
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Letakkan di sini
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sistem_akademik.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sistem_akademik.wsgi.application'


# ==============================================================================
# DATABASE
# Menggunakan dj_database_url untuk membaca env var DATABASE_URL dari Render
# ==============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,
        'USER': 'alan',
        'PASSWORD': 'alan',
        'HOST': '165.22.106.176',  # or IP address of the DB server
        'PORT': '3306',
        # 'OPTIONS': {
        #     'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        # }
    }
}

# DATABASES = {
#     'default': dj_database_url.config(
#         # Jika DATABASE_URL tidak ada, gunakan SQLite sebagai fallback (untuk lokal)
#         default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
#         conn_max_age=600
#     )
# }


# ==============================================================================
# VALIDASI PASSWORD & INTERNASIONALISASI
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'id' # Ganti ke 'id' agar lebih sesuai
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True


# ==============================================================================
# STATIC & MEDIA FILES
# Konfigurasi untuk WhiteNoise agar bisa menyajikan file CSS/JS/Gambar Anda
# ==============================================================================

STATIC_URL = '/static/'
# Tempat di mana `collectstatic` akan mengumpulkan semua file statis
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ==============================================================================
# PENGATURAN LAIN-LAIN
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '[{levelname}] {name} – {message}', 'style': '{',},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple',},
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO',},
        'core': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False,},
    },
}

# ==============================================================================
# KONFIGURASI DJANGO-JAZZMIN
# Letakkan ini di bagian paling bawah file settings.py Anda
# ==============================================================================

JAZZMIN_SETTINGS = {
    # Judul yang muncul di tab browser dan di header halaman login
    "site_title": "Administrasi Takhossus",

    # Teks header di halaman admin
    "site_header": "Sistem Akademik",

    # Teks yang muncul di sebelah logo (jika ada)
    "site_brand": "Takhossus",

    # Path ke logo Anda di folder static. Ganti jika perlu.
    # Harus diawali dengan nama aplikasi Anda ('core/')
    "site_logo": "core/images/Takhossus.png",

    # Logo untuk halaman login
    "login_logo": "core/images/Takhossus.png",

    # Teks sambutan di halaman utama admin
    "welcome_sign": "Selamat datang di Administrasi Sistem Akademik Takhossus",

    # Copyright di footer
    "copyright": "Sistem Akademik Takhossus",

    # Mengatur urutan dan pengelompokan model di sidebar
    "order_with_respect_to": [
        # Grup pertama: Manajemen Akademik
        "core", "core.Santri", "core.RiwayatTes", "core.SKS", "core.Fan",
        
        # Grup kedua: Otentikasi
        "auth.User", "auth.Group",
    ],

    # Menambahkan ikon untuk setiap model (menggunakan Font Awesome)
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        
        "core.Santri": "fas fa-user-graduate",
        "core.RiwayatTes": "fas fa-check-double",
        "core.SKS": "fas fa-book-open",
        "core.Fan": "fas fa-layer-group",
    },

    # Menyembunyikan model tertentu (jika perlu)
    "hide_models": [],

    # Menyembunyikan aplikasi tertentu
    "hide_apps": [],

    # Menambahkan link custom di menu atas
    "topmenu_links": [
        # Link kembali ke dashboard utama aplikasi Anda
        {"name": "Lihat Situs",  "url": "/", "new_window": True},

        # Link ke halaman admin (sudah otomatis ada)
        {"name": "Admin", "url": "/admin", "permissions": ["auth.view_user"]},

        # Model App
        {"app": "core"},
    ],

    # Opsi UI
    "show_ui_builder": True, # Sembunyikan UI builder agar lebih bersih
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-lightblue",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": True,
    "sidebar_nav_flat_style": False,
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary"
    },
    "custom_css": "core/static/core/css/jazzmin_custom.css"
}