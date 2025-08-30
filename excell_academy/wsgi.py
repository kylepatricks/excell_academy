"""
WSGI config for excell_academy project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

# school_management/wsgi.py
import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excell_academy.settings.prod')

application = get_wsgi_application()

# Add WhiteNoise for static files
application = WhiteNoise(application, root=os.path.join(os.path.dirname(__file__), 'staticfiles'))
