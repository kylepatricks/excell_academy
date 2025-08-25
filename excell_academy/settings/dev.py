from .common import *
from dotenv import load_dotenv


load_dotenv()


SECRET_KEY='616d612602596bdb203c129f354aa1fd48dff88a0a2ae2e703'


DEBUG =False

SECRET_KEY = 'django-insecure-tpwdbv98e^f-71-mp=uei40^967uy($k^jf=*3t)@h0+e-y=$7'

ALLOWED_HOSTS =['https://excell-academy.onrender.com','excell-academy.onrender.com']

EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST='smtp.gmail.com'
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER='kyleasante4@gmail.com'
EMAIL_HOST_PASSWORD='vkpxxfnpjetvxble'
DEFAULT_FROM_EMAIL='mysmsapp@gmail.com'


PAYSTACK_SECRET_KEY=os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_PUBLIC_KEY=os.getenv('PAYSTACK_PUBLIC_KEY')
PAYSTACK_BASE_URL =os.getenv('PAYSTACK_BASE_URL')

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