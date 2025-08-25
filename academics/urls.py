# academics/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('grades/', views.enter_grades, name='enter_grades'),
    path('report-cards/', views.generate_report_cards, name='generate_report_cards'),
]