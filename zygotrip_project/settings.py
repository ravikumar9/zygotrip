from pathlib import Path
import logging
import os
import socket

BASE_DIR = Path(__file__).resolve().parent.parent


# ======================================================
# CORE
# ======================================================

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-key")

DEBUG = True  # TEMPORARILY ENABLED FOR LOCAL VALIDATION

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver", "*"]

SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = False  # TEMPORARILY DISABLED FOR HTTP TESTING
CSRF_COOKIE_SECURE = False  # TEMPORARILY DISABLED FOR HTTP TESTING


# ======================================================
# INSTALLED APPS
# ======================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # project apps
    "apps.accounts",
    "apps.core",
    "apps.hotels",
    "apps.rooms",
    "apps.meals",
    "apps.pricing",
    "apps.booking",
    "apps.payments",
    "apps.wallet",
    "apps.promos",
    "apps.reviews",
    "apps.buses",
    "apps.packages",
    "apps.flights",
    "apps.trains",
    "apps.cabs",
    "apps.inventory",
    "apps.dashboard_owner",
    "apps.dashboard_admin",
    "apps.dashboard_finance",

    # celery
    "django_celery_beat",
    "django_celery_results",
]


# ======================================================
# MIDDLEWARE
# ======================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",

    "apps.core.middleware.RateLimitMiddleware",
    "apps.core.middleware.StructuredLoggingMiddleware",
]


ROOT_URLCONF = "zygotrip_project.urls"
WSGI_APPLICATION = "zygotrip_project.wsgi.application"


# ======================================================
# TEMPLATES
# ======================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ======================================================
# DATABASE
# ======================================================

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

if POSTGRES_DB and POSTGRES_USER and POSTGRES_PASSWORD:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": POSTGRES_DB,
            "USER": POSTGRES_USER,
            "PASSWORD": POSTGRES_PASSWORD,
            "HOST": POSTGRES_HOST,
            "PORT": POSTGRES_PORT,
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ======================================================
# PASSWORD VALIDATORS
# ======================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ======================================================
# INTERNATIONALIZATION
# ======================================================

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"

USE_I18N = True
USE_TZ = True

CURRENCY_CODE = "INR"
CURRENCY_SYMBOL = "₹"
REGION_DEFAULT = "IN"


# ======================================================
# STATIC + MEDIA
# ======================================================

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_MANIFEST_STRICT = False

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ======================================================
# AUTH
# ======================================================

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"


# ======================================================
# BUSINESS LOGIC
# ======================================================

SERVICE_FEE_RATE = 0.08
GST_RATE = 0.12


# ======================================================
# REDIS CACHE
# ======================================================

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
USE_REDIS_CACHE = os.getenv("USE_REDIS_CACHE", "false").lower() in {"1", "true", "yes"}

def _redis_available(host, port):
    try:
        socket.create_connection((host, int(port)), timeout=0.3).close()
        return True
    except OSError:
        logging.getLogger("zygotrip").warning(
            "Redis unreachable. Falling back to local memory cache.")
        return False

if USE_REDIS_CACHE and _redis_available(REDIS_HOST, REDIS_PORT):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "zygotrip-fallback",
        }
    }


# ======================================================
# CELERY
# ======================================================

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/2"

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 1800
CELERY_RESULT_EXPIRES = 3600

CELERY_BEAT_SCHEDULE = {
    "cleanup-expired-bookings": {
        "task": "apps.core.tasks.cleanup_expired_bookings",
        "schedule": 300.0,
    },
    "generate-daily-reports": {
        "task": "apps.core.tasks.generate_daily_reports",
        "schedule": 86400.0,
    },
}


# ======================================================
# LOGGING
# ======================================================

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure handlers based on environment
# Development: console only (avoids file locking issues on Windows)
# Production: console + rotating file
if DEBUG:
    LOGGING_HANDLERS = ["console"]
else:
    LOGGING_HANDLERS = ["console", "file"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "apps.core.logging_formatters.JSONFormatter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "zygotrip.log",
            "maxBytes": 10485760,
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": LOGGING_HANDLERS,
            "level": "INFO",
            "propagate": False,
        },
        "zygotrip": {
            "handlers": LOGGING_HANDLERS,
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


# ======================================================
# RATE LIMIT
# ======================================================

RATE_LIMIT_CONFIG = {
    "enabled": False,
    "window_size": 60,
    "requests_per_window": {
        "default": 100,
        "search": 50,
        "booking": 20,
        "payment": 10,
    },
    "redis_key_prefix": "ratelimit:",
}


# ======================================================
# DEFAULT FIELD
# ======================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ======================================================
# FEATURE FLAGS - MARKETPLACE FEATURES
# ======================================================

FEATURE_FLAGS = {
    # Core features
    'FLIGHTS_ENABLED': False,
    'TRAINS_ENABLED': False,
    'CABS_ENABLED': True,
    'HOTELS_ENABLED': True,
    'BUSES_ENABLED': True,
    'PACKAGES_ENABLED': True,
    
    # Marketplace features
    'PROPERTY_IMAGES_ENABLED': True,
    'ROOM_TYPES_ENABLED': True,
    'MEAL_PLANS_ENABLED': True,
    'PROPERTY_OFFERS_ENABLED': True,
    'RATING_BREAKDOWN_ENABLED': True,
    'CATEGORIES_ENABLED': True,
    
    # Advanced features
    'OWNER_DASHBOARD_UPLOADS': True,
    'DYNAMIC_PRICING': True,
    'MULTI_IMAGE_GALLERY': True,
    'OFFER_SYSTEM': True,
    'ADVANCED_FILTERS': True,
}