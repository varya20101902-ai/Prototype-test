"""
Настройки Django для проекта Quizsite.

Файл создан командой django-admin startproject с использованием Django 6.0.2.
"""

import os
from pathlib import Path

# Пути внутри проекта строятся так: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(env_path):
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file(BASE_DIR / ".env")


# Быстрые настройки для разработки, не предназначены для продакшена.

# Важно: храните секретный ключ для продакшена в безопасном месте.
SECRET_KEY = 'django-insecure-f0a-kv4l90^35t6ldm9a44-ej1ao5w+22o!qmsw2f0n3m@=(8l'

# Важно: не включайте DEBUG в продакшене.
DEBUG = True

ALLOWED_HOSTS = ['prototype-test-aowp.onrender.com', 'localhost', '127.0.0.1']


# Приложения проекта

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Quiz.apps.QuizConfig',
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

ROOT_URLCONF = 'Quizsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Quizsite.wsgi.application'


# База данных

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Проверка паролей

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


# Локализация

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Статические файлы

STATIC_URL = 'static/'

# Путь, который будет виден в браузере (например, /media/file.jpg)
MEDIA_URL = '/media/'

# Физический путь на диске к папке с файлами
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")
HF_MODEL = os.environ.get("HF_MODEL", "openai/gpt-oss-20b:novita")
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
