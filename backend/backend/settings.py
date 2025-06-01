from pathlib import Path
import os

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dummy-secret-key-for-dev")

# === BASE SETTINGS ===
BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = True  # Aktifkan hanya untuk development

ALLOWED_HOSTS = ['*']  # Kosongkan untuk local dev, tambahkan domain/IP saat di-deploy

ROOT_URLCONF = 'backend.urls'  # Pastikan ini sesuai dengan nama project kamu

# === DATABASE ===
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# === INSTALLED APPS ===
INSTALLED_APPS = [
    # Default Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',

    # Your apps
    'produk',
]

# === MIDDLEWARE ===
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# === TEMPLATES ===
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Tambah path ke template folder jika perlu
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

# === STATIC FILES ===
STATIC_URL = '/static/'

# === REST FRAMEWORK CONFIG ===
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}