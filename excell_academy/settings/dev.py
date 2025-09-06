import dj_database_url
from .common import *
from dotenv import load_dotenv
from decouple import config, Csv
import logging


load_dotenv()


SECRET_KEY=os.getenv('SECRET_KEY')


DEBUG =config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

if DEBUG:
   
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']
else:
    
    RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_EXTERNAL_HOSTNAME:
        ALLOWED_HOSTS = [RENDER_EXTERNAL_HOSTNAME, 'https://excell-academy.onrender.com']  
    else:
        ALLOWED_HOSTS = []

CSRF_TRUSTED_ORIGINS = ['https://excell-academy.onrender.com']



EMAIL_BACKEND=config('EMAIL_BACKEND')
EMAIL_HOST=config('EMAIL_HOST')
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD=config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL=config('DEFAULT_FROM_EMAIL')



PAYSTACK_SECRET_KEY=os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_PUBLIC_KEY=os.getenv('PAYSTACK_PUBLIC_KEY')
PAYSTACK_BASE_URL =os.getenv('PAYSTACK_BASE_URL')

database_url = config('DATABASE_URL', default=None)

if database_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600, 
            ssl_require=True 
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }



CSRF_TRUSTED_ORIGINS = [
    'https://excell-academy.onrender.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

CORS_ALLOWED_ORIGINS = [
    "https://excell-academy.onrender.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]