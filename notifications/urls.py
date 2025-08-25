# notifications/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('send/', views.send_notification, name='send_notification'),
    path('count/', views.notification_count, name='notification_count')
]