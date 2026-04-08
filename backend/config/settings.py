from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "100.80.107.87",
    "192.168.0.166",
]

DEFAULT_CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "https://localhost",
    "http://127.0.0.1",
    "https://127.0.0.1",
    "https://100.80.107.87",
    "https://192.168.0.166",
]


def _split_env_list(value):
    return [item.strip() for item in value.split(",") if item.strip()]


def _merge_unique(items):
    return list(dict.fromkeys(items))


SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
DEBUG = os.getenv("DEBUG", "0") == "1"
ALLOWED_HOSTS = _merge_unique(DEFAULT_ALLOWED_HOSTS + _split_env_list(os.getenv("ALLOWED_HOSTS", "")))
CSRF_TRUSTED_ORIGINS = _merge_unique(
    DEFAULT_CSRF_TRUSTED_ORIGINS + _split_env_list(os.getenv("CSRF_TRUSTED_ORIGINS", ""))
)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
    "reports",
    "imports",
    "publishing",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "raport"),
        "USER": os.getenv("POSTGRES_USER", "raport"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "raport"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

LANGUAGE_CODE = "pl"
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "0") == "1"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "0") == "1"
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "0") == "1"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

GRAFANA_EMBED_URL = os.getenv(
    "GRAFANA_EMBED_URL",
    "/grafana/d/raport-zarzadczy-zarzad/raport-zarzadczy-zarzad?orgId=1&kiosk",
)
GRAFANA_DASHBOARD_URL = os.getenv(
    "GRAFANA_DASHBOARD_URL",
    "/grafana/d/raport-zarzadczy-zarzad/raport-zarzadczy-zarzad?orgId=1",
)
