import os
from pathlib import Path
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rag_app.apps.RagAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'archivebot_project.urls'

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

WSGI_APPLICATION = 'archivebot_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Data directories
DATA_DIR = BASE_DIR / "data"
RAW_CORPUS_DIR = DATA_DIR / "raw_corpus"
TEXT_CORPUS_DIR = DATA_DIR / "text_corpus"
CHUNKED_CORPUS_DIR = DATA_DIR / "chunked_corpus"

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Create static directory if it doesn't exist
STATIC_APP_DIR = BASE_DIR / "rag_app" / "static"
os.makedirs(STATIC_APP_DIR, exist_ok=True)
os.makedirs(STATIC_APP_DIR / "rag_app" / "css", exist_ok=True)
os.makedirs(STATIC_APP_DIR / "rag_app" / "js", exist_ok=True)
os.makedirs(STATIC_APP_DIR / "rag_app" / "images", exist_ok=True)

STATICFILES_DIRS = [
    STATIC_APP_DIR,
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Create data directories
for directory in [DATA_DIR, RAW_CORPUS_DIR, TEXT_CORPUS_DIR, CHUNKED_CORPUS_DIR]:
    os.makedirs(directory, exist_ok=True) 