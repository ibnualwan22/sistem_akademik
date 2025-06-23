# settings.py - VERSI FINAL UNTUK DEPLOYMENT DI RENDER.COM

from pathlib import Path
import os
import dj_database_url # Diperlukan untuk membaca DATABASE_URL dari Render

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# PENGATURAN KUNCI, DEBUG, DAN HOST
# Ini satu-satunya tempat untuk mengatur variabel-variabel ini.
# ==============================================================================

# Ambil Secret Key dari environment variable.
# Ini WAJIB diatur di Render untuk keamanan.
SECRET_KEY = os.environ.get('SECRET_KEY')

# DEBUG=True jika ada env var DEBUG=True, jika tidak maka otomatis False.
# Di Render, JANGAN set variabel DEBUG agar otomatis False (aman).
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Untuk static files di produksi
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
        'DIRS': [],
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
    'default': dj_database_url.config(
        # Jika DATABASE_URL tidak ada, gunakan SQLite sebagai fallback (untuk lokal)
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600
    )
}


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