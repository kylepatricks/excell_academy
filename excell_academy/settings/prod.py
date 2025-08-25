"""
Production settings for Excel International Academy
Deployment: Render.com
"""

import os
import dj_database_url
import logging
from .common import *


DEBUG = False


SECRET_KEY = os.environ['SECRET_KEY']


LOWED_HOSTS =[]


EMAIL_BACKEND=os.environ['EMAIL_BACKEND']
EMAIL_HOST=os.environ['EMAIL_hOST']
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD=os.environ['EMAIL_HOST_PASSWORD']
DEFAULT_FROM_EMAIL=os.environ['DEFAULT_FROM_EMAIL']



PAYSTACK_SECRET_KEY=os.environ['PAYSTACK_SECRET_KEY']
PAYSTACK_PUBLIC_KEY=os.environ['PAYSTACK_PUBLIC_KEY']
PAYSTACK_BASE_URL =os.environ['PAYSTACK_BASE_URL']


SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'


ENVIRONMENT = 'production'
logger = logging.getLogger(__name__)

DATABASES = {
    'default': dj_database_url.config()
}



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'excel_academy': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

EXCEL_ACADEMY = {
    'ENVIRONMENT': ENVIRONMENT,
    'SUPPORT_EMAIL': 'support@excelacademy.edu',
    'ADMIN_EMAIL': 'admin@excelacademy.edu',
    'PAYMENT_TIMEOUT': 30,  # minutes
}

HEALTH_CHECK = {
    'DATABASE': 'excell_academy.db_health_check',
}

def db_health_check():
    """Custom database health check"""
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception:
        return False

logger.info(f"Excel Academy production settings loaded for {ENVIRONMENT} environment")