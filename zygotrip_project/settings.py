from pathlib import Path
import logging
import os
import socket

BASE_DIR = Path(__file__).resolve().parent.parent


# ======================================================
# CORE - PRODUCTION SECURITY
# ======================================================

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-key")

# DEBUG MODE - default to safe local development unless explicitly disabled
DEBUG = os.getenv("DEBUG", "true").lower() in {"1", "true", "yes"}

if SECRET_KEY == "unsafe-dev-key" and not DEBUG:
    import sys
    print(
        "\n[CRITICAL] DJANGO_SECRET_KEY is not set! "
        "Running with an unsafe dev key in a non-DEBUG environment is a security risk.\n",
        file=sys.stderr,
    )
    raise RuntimeError(
        "Set the DJANGO_SECRET_KEY environment variable before running in production."
    )

# ALLOWED_HOSTS - Must be explicitly configured in production
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")

# CSP: unsafe-inline is a necessary dev convenience but should be tightened in
# production by adding a nonce-based approach. Tracked as TODO: prod-csp-hardening.
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    # TODO prod-csp-hardening: replace unsafe-inline with nonce
    "script-src": ("'self'", "'unsafe-inline'"),
    "style-src": ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com"),
    "font-src": ("'self'", "https://fonts.gstatic.com"),
    "img-src": ("'self'", "data:", "https:"),
}

# HTTPS enforcement in production
# FORCE SAFE DEV MODE: When DEBUG=True, disable all SSL
SECURE_SSL_REDIRECT = False if DEBUG else True
SESSION_COOKIE_SECURE = False if DEBUG else True
CSRF_COOKIE_SECURE = False if DEBUG else True
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000  # 1 year in production only
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Log safe dev mode
if DEBUG:
    print("=" * 60)
    print("[DEV] RUNNING IN SAFE DEV MODE (LOCAL TESTING)")
    print("=" * 60)
    print("[OK] SSL redirect disabled")
    print("[OK] Secure cookies disabled")
    print("[OK] HSTS disabled")
    print("[OK] Celery eager execution enabled")
    print("=" * 60)


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

    # Third-party
    "rest_framework",
    "django_filters",
    "django_extensions",

    # project apps
    "apps.accounts",
    "apps.core",
    "apps.search",
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
    "apps.offers",
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
# DATABASE - FORCE POSTGRESQL ONLY
# ======================================================

POSTGRES_DB = os.getenv("POSTGRES_DB", "zygotrip")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
        # CONN_MAX_AGE: reuse connections across requests (seconds).
        # 60s is safe for most deployments. Set to 0 in tests.
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        # PostgreSQL-specific options for production performance
        "OPTIONS": {
            # Set statement_timeout to avoid runaway queries (10 seconds)
            "options": "-c statement_timeout=10000",
        },
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

# PHASE 9: FORCE SAFE DEV MODE - Disable Celery beat in DEBUG, run tasks eagerly
if DEBUG:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BEAT_SCHEDULE = {}  # Disable all scheduled tasks in dev
else:
    CELERY_TASK_ALWAYS_EAGER = False
    CELERY_TASK_EAGER_PROPAGATES = False
    CELERY_BEAT_SCHEDULE = {
        "release-expired-booking-holds": {
            "task": "core.tasks.release_expired_booking_holds",
            "schedule": 120.0,  # Every 2 minutes
        },
        "cleanup-expired-bookings": {
            "task": "core.tasks.cleanup_expired_bookings",
            "schedule": 300.0,  # Every 5 minutes
        },
        "generate-daily-reports": {
            "task": "core.tasks.generate_daily_reports",
            "schedule": 86400.0,  # Daily
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
    "enabled": True,   # FIXED: Rate limiting must be ON by default
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

# django-extensions already in INSTALLED_APPS above (removed stray append)

# ======================================================
# DJANGO REST FRAMEWORK
# ======================================================

REST_FRAMEWORK = {
    # Pagination: standardised across all API endpoints
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,

    # Authentication: session + token (mobile-ready)
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],

    # Permissions: read-only for unauthenticated, full for authenticated
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],

    # Filtering, ordering, search via django-filter
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    # Standardised JSON renderer only (no browsable API in production)
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ] if not DEBUG else [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],

    # Throttling (integrates with existing RATE_LIMIT_CONFIG)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/minute',
        'user': '300/minute',
    },

    # Versioning: URL-based (/api/v1/...)
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1'],

    # Exception handling: return structured error responses
    'EXCEPTION_HANDLER': 'apps.core.api_validators.drf_exception_handler',
}
