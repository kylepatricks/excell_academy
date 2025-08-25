# finance/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('invoices/', views.view_invoices, name='view_invoices'),
    path('pay-invoice/<int:invoice_id>/', views.pay_invoice, name='pay_invoice'),
    path('verify-payment/', views.verify_paystack_payment, name='verify_paystack_payment'),
    path('payment-success/', views.handle_successful_payment, name='payment_success'),
    path('payment-history/', views.payment_history, name='payment_history'),
    path('check-config/', views.check_paystack_config, name='check_paystack_config'),
]