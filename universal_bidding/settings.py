"""
Django settings for universal_bidding project.
"""

import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

_secret_key = os.environ.get('DJANGO_SECRET_KEY')
if not _secret_key:
    if os.environ.get('DJANGO_DEBUG', 'False') == 'True':
        # Development-only fallback — never used in production
        _secret_key = 'django-insecure-dev-only-do-not-use-in-production'
    else:
        raise ValueError(
            "DJANGO_SECRET_KEY environment variable is not set. "
            "Set it to a long random string before running in production."
        )
SECRET_KEY = _secret_key

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

_allowed_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(',') if h.strip()] or (['localhost', '127.0.0.1'] if DEBUG else [])
_trusted_origins = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _trusted_origins.split(',') if o.strip()]

INSTALLED_APPS = [
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'accounts',
    'auctions',
    'bidding',
    'notifications',
    'fraud_detection',
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

ROOT_URLCONF = 'universal_bidding.urls'
ASGI_APPLICATION = 'universal_bidding.asgi.application'

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

WSGI_APPLICATION = 'universal_bidding.wsgi.application'

_database_url = os.environ.get('DATABASE_URL', '').strip()
_db_engine = os.environ.get('DB_ENGINE', '').strip().lower()
_use_postgres = _db_engine in {'postgres', 'postgresql'} or all(
    os.environ.get(key) for key in ('POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD')
)
_conn_max_age = int(os.environ.get('DB_CONN_MAX_AGE', '60'))

if _database_url:
    parsed = urlparse(_database_url)
    if parsed.scheme not in {'postgres', 'postgresql', 'postgresql_psycopg2'}:
        raise ValueError("DATABASE_URL must use postgres:// or postgresql://")

    db_options = {}
    ssl_mode = parse_qs(parsed.query).get('sslmode', [None])[0]
    if ssl_mode:
        db_options['sslmode'] = ssl_mode

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': unquote((parsed.path or '').lstrip('/')),
            'USER': unquote(parsed.username or ''),
            'PASSWORD': unquote(parsed.password or ''),
            'HOST': parsed.hostname or 'localhost',
            'PORT': str(parsed.port or 5432),
            'CONN_MAX_AGE': _conn_max_age,
            'OPTIONS': db_options,
        }
    }
elif _use_postgres:
    _db_sslmode = os.environ.get('POSTGRES_SSLMODE', '').strip()
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'bidding_db'),
            'USER': os.environ.get('POSTGRES_USER', 'bidding_user'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', 'db'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': _conn_max_age,
            'OPTIONS': {'sslmode': _db_sslmode} if _db_sslmode else {},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'auctions:home'
LOGOUT_REDIRECT_URL = 'auctions:home'

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'True') == 'True'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '3600'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# IP-based rate limiting for bids (max bids per minute per IP)
BID_RATE_LIMIT = 10

REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BEAT_SCHEDULE = {
    'close-expired-auctions': {
        'task': 'auctions.tasks.close_expired_auctions',
        'schedule': 60.0,
    },
}
