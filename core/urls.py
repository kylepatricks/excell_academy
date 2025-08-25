# core/urls.py
from django.urls import path

from core import admin_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('facilities/', views.facilities_list, name='facilities'),
    path('apply/', views.apply, name='apply'),
    path('contact/', views.contact, name='contact'),

    # Admin application management URLs
    path('applications/', admin_views.application_list, name='application_list'),
    path('applications/<int:pk>/', admin_views.application_detail, name='application_detail'),
]