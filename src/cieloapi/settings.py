import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-default-only-for-ci-and-local-dev")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'apps.usuarios',
    'apps.integraciones',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'cieloapi.middleware.CorrelationIDMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --- API SETTINGS ---
APPEND_SLASH = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.integraciones.authentication.APIKeyAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Rate limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',      # Usuarios no autenticados
        'user': '200/minute',     # Usuarios autenticados
    },
}

AUTH_USER_MODEL = "usuarios.User"


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
}

ROOT_URLCONF = 'cieloapi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'apps/templates',  
        ],
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


WSGI_APPLICATION = 'cieloapi.wsgi.application'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "cielo_db"),
        "USER": os.getenv("DB_USER", "cielo_user"),
        "PASSWORD": os.getenv("DB_PASS", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    },
}

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

LANGUAGE_CODE = "es"
USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'America/Bogota'

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "https://localhost:3000,https://localhost:9002").split(",")

CSRF_TRUSTED_ORIGINS = [
    "https://cieloapi.lambdaanalytics.co",
    "http://localhost:9002",
    "http://localhost:3000",
]

# --- SUPPLOS API SETTINGS ---
SUPPLOS_API_URL = os.getenv("SUPLOS_API_URL", "https://apicoronaqas.suplos.com")
SUPPLOS_EMAIL = os.getenv("SUPLOS_API_EMAIL", "")
SUPPLOS_PASSWORD = os.getenv("SUPLOS_API_PASSWORD", "")

# --- CACHE SETTINGS ---
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': BASE_DIR / 'cache',
        'TIMEOUT': 300,  # 5 minutos por defecto
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# --- CELERY SETTINGS ---
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TRACK_STARTED = True
CELERY_RESULT_EXPIRES = 3600  # Resultados expiran en 1 hora

# --- CELERY BEAT SCHEDULE ---
CELERY_BEAT_SCHEDULE = {
    'limpiar-registros-antiguos': {
        'task': 'apps.integraciones.tasks.limpiar_registros_antiguos',
        'schedule': 86400,  # Cada 24 horas
    },
}

# --- AZURE DOCUMENT INTELLIGENCE ---
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "")
AZURE_DOCUMENT_INTELLIGENCE_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")

# --- AZURE OPENAI ---
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")

# Modelo estructurador (OCR / correos)
AZURE_OPENAI_STRUCTURING_DEPLOYMENT = os.getenv("AZURE_OPENAI_STRUCTURING_DEPLOYMENT", "gpt-4.1-structuring-suplos")
AZURE_OPENAI_STRUCTURING_API_VERSION = os.getenv("AZURE_OPENAI_STRUCTURING_API_VERSION", "2025-01-01-preview")

# Modelo orquestador (agente principal)
AZURE_OPENAI_ORCHESTRATOR_DEPLOYMENT = os.getenv("AZURE_OPENAI_ORCHESTRATOR_DEPLOYMENT", "gpt-5.2-chat-orchestrator-suplos")
AZURE_OPENAI_ORCHESTRATOR_API_VERSION = os.getenv("AZURE_OPENAI_ORCHESTRATOR_API_VERSION", "2025-04-01-preview")

# --- LOGGING JSON ESTRUCTURADO ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'cieloapi.logging_formatter.JSONFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'loggers': {
        'apps.integraciones': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.usuarios': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
