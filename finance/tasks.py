# finance/tasks.py - Place in finance/ directory
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Invoice, Payment
import logging

logger = logging.getLogger(__name__)

def process_pending_payments():
    """Process pending manual payments"""
    try:
        pending_payments = Payment.objects.filter(
            confirmed_by__isnull=True,
            payment_method__in=['bank_transfer', 'mobile_money']
        )
        
        logger.info(f"Found {pending_payments.count()} pending payments")
        
        for payment in pending_payments:
            # Here you would integrate with your payment verification system
            logger.info(f"Processing pending payment: {payment.id} - {payment.amount}")
            
    except Exception as e:
        logger.error(f"Error processing payments: {e}")

def send_payment_reminders():
    """Send payment reminder emails"""
    try:
        overdue_invoices = Invoice.objects.filter(
            status__in=['pending', 'overdue'],
            due_date__lt=timezone.now().date()
        )
        
        logger.info(f"Found {overdue_invoices.count()} overdue invoices")
        
        for invoice in overdue_invoices:
            subject = f'Payment Reminder: Invoice #{invoice.invoice_number}'
            message = f'''
            Dear {invoice.student.parent.user.get_full_name()},
            
            This is a reminder that your invoice #{invoice.invoice_number} 
            for {invoice.student.user.get_full_name()} is overdue.
            
            Amount: GHS{invoice.amount}
            Due Date: {invoice.due_date}
            
            Please make payment at your earliest convenience.
            
            Best regards,
            Excel International Academy
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [invoice.student.parent.user.email],
                fail_silently=True,
            )
            
            logger.info(f"Sent reminder for invoice: {invoice.invoice_number}")
            
    except Exception as e:
        logger.error(f"Error sending reminders: {e}")