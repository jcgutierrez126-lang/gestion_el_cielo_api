from cieloapi.settings import *  # noqa

# Valores mínimos requeridos en CI (donde no hay .env)
SECRET_KEY = 'django-insecure-test-only-key-not-for-production'
DEBUG = True

# Usar SQLite en memoria para tests — no requiere SQL Server
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Cache en memoria local — necesario para tests de reset de contraseña
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# URL del frontend usada en correos corporativos
FRONTEND_URL = "localhost:8000"
