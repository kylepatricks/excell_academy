# academics/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('grades/', views.enter_grades, name='enter_grades'),
    path('report-cards/', views.generate_report_cards, name='generate_report_cards'),
    path('report-cards/generate-pdf/<int:report_card_id>/', views.generate_report_card_pdf, name='generate_report_card_pdf'),
    path('report-cards/download/<int:report_card_id>/', views.download_report_card, name='download_report_card'),
    path('report-cards/preview/<int:report_card_id>/', views.preview_report_card, name='preview_report_card'),
    path('report-cards/list/', views.report_card_list, name='report_card_list'),
    path('report-cards/<int:report_card_id>/', views.report_card_detail, name='report_card_detail'),
    path('report-cards/update-remarks/<int:report_card_id>/', views.update_report_card_remarks, name='update_report_card_remarks')
]