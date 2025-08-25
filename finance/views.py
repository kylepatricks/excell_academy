# finance/views.py
import json
from django.http import JsonResponse
from django.utils import timezone
import uuid
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from requests import request
from accounts.models import CustomUser
from finance.utils import get_safe_invoice
from .models import Invoice, Payment
from .paystack_utils import paystack_api
from django.urls import reverse

@login_required
@user_passes_test(lambda u: u.user_type == 'parent')
def view_invoices(request):
    parent = request.user.parent_profile.first()
    children = parent.children.all()
    
    # Get all invoices
    invoices = Invoice.objects.filter(student__in=children).order_by('-issue_date')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    # Calculate counts for the badge
    pending_count = invoices.filter(status='pending').count()
    paid_count = invoices.filter(status='paid').count()
    overdue_count = invoices.filter(status='overdue').count()
    partial_count = invoices.filter(status='partial').count()
    
    context = {
        'invoices': invoices,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'paid_count': paid_count,
        'overdue_count': overdue_count,
        'partial_count': partial_count,
        'total_invoices': invoices.count(),
    }
    return render(request, 'finance/invoices.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'parent')
def pay_invoice(request, invoice_id):
    try:
        # Convert string UUID to UUID object if needed
        if isinstance(invoice_id, str) and '-' in invoice_id:
            invoice_id = uuid.UUID(invoice_id)
        
        invoice = get_object_or_404(Invoice, id=invoice_id, student__parent__user=request.user)
        # Generate a new unique reference for each payment attempt
        invoice.generate_paystack_reference()
        invoice.save()

    except (ValueError, Invoice.DoesNotExist):
        messages.error(request, 'Invoice not found or access denied.')
        return redirect('view_invoices')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        if payment_method == 'paystack':
            return redirect('initiate_paystack_payment', invoice_id=invoice.id)
        elif payment_method in ['bank_transfer', 'mobile_money']:
            # Process other payment methods
            amount = request.POST.get('amount', invoice.amount)
            
            payment = Payment.objects.create(
                invoice=invoice,
                amount=amount,
                payment_method=payment_method,
                receipt_number=f"PMT-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                confirmed_by=None
            )
            
            # Create notification for admin to confirm payment
            from notifications.models import Notification
            admin_users = CustomUser.objects.filter(user_type='admin', is_active=True)
            for admin in admin_users:
                Notification.objects.create(
                    recipient=admin,
                    title='Payment Requires Confirmation',
                    message=f'A {payment_method} payment of GHS{amount} has been made for invoice #{invoice.invoice_number}',
                    notification_type='fee',
                    related_url=f'/admin/finance/payment/{payment.id}/'
                )
            
            messages.success(request, 'Payment submitted. It will be confirmed by administration shortly.')
            return redirect('view_invoices')
        
    # Check if key is properly configured
    if not settings.PAYSTACK_PUBLIC_KEY or settings.PAYSTACK_PUBLIC_KEY == 'pk_test_':
        messages.error(request, "Paystack payment is not configured properly. Please contact support.")


    context = {
        'invoice': invoice,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
    }
    return render(request, 'finance/pay_invoice.html', context)



def check_paystack_config(request):
    return JsonResponse({
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        'paystack_secret_key_set': bool(settings.PAYSTACK_SECRET_KEY),
        'debug_mode': settings.DEBUG,
    })

@login_required
@login_required
def paystack_payment(request, invoice_id):
    """Initiate Paystack payment"""
    try:
        # Get the invoice with proper relationship checking
        invoice = get_object_or_404(
            Invoice, 
            id=invoice_id, 
            student__parent__user=request.user
        )
    
    except Invoice.DoesNotExist:
        messages.error(request, 'Invoice not found or access denied.')
        return redirect('view_invoices')
    
    if invoice.status == 'paid':
        messages.warning(request, 'This invoice has already been paid.')
        return redirect('view_invoices')
    
    # Generate callback URL
    current_site = get_current_site(request)
    callback_url = f"https://{current_site.domain}{reverse('paystack_callback')}"
    
    # Prepare metadata - Now using proper ID fields
    metadata = {
        'invoice_id': invoice.id,
        'student_id': invoice.student.id,  # Now this will work
        'parent_id': invoice.student.parent.id,  # This will also work
        'custom_fields': [
            {
                'display_name': "Invoice Number",
                'variable_name': "invoice_number",
                'value': invoice.invoice_number
            },
            {
                'display_name': "Student Name",
                'variable_name': "student_name",
                'value': invoice.student.user.get_full_name()
            }
        ]
    }
    
    # Initialize Paystack transaction
    response = paystack_api.initialize_transaction(
        email=request.user.email,
        amount=invoice.amount,
        reference=invoice.paystack_reference,
        callback_url=callback_url,
        metadata=metadata
    )
    
    if response.get('status'):
        return redirect(response['data']['authorization_url'])
    else:
        messages.error(request, f"Payment initialization failed: {response.get('message', 'Unknown error')}")
        return redirect('pay_invoice', invoice_id=invoice.id)
    

def handle_successful_payment(payment_data):
    """Process successful payment"""
    try:
        metadata = payment_data.get('metadata', {})
        invoice_id = metadata.get('invoice_id')
        
        if invoice_id:
            invoice = Invoice.objects.get(id=invoice_id)
            
            # Create payment record
            payment = Payment.objects.create(
                invoice=invoice,
                amount=payment_data['amount'], 
                payment_method='paystack',
                payment_date=timezone.now(),
                transaction_id=payment_data['reference'],
                receipt_number=f"PAYSTACK_{payment_data['reference']}",
                paystack_reference=payment_data['reference'],
                paystack_authorization=payment_data.get('authorization'),
                confirmed_by=None  # Auto-confirmed by Paystack
            )
            
            # Update invoice status
            if payment.amount >= invoice.amount:
                invoice.status = 'paid'
            else:
                invoice.status = 'partial'
            invoice.save()
            
            # Send confirmation email
            send_payment_confirmation(invoice, payment)
            
            return render(request, 'finance/payment_success.html', {
                'invoice': invoice,
                'payment': payment,
                'payment_data': payment_data
            })
    
    except Exception as e:
        # Log the error
        print(f"Payment processing error: {e}")
        
    return render(request, 'finance/payment_error.html', {
        'message': 'Error processing payment. Please contact support.'
    })
    

def handle_failed_payment(payment_data):
    """Handle failed payment"""
    return render(request, 'finance/payment_error.html', {
        'message': payment_data.get('gateway_response', 'Payment failed. Please try again.'),
        'payment_data': payment_data
    })

def send_payment_confirmation(invoice, payment):
    """Send payment confirmation email"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    subject = f'Payment Confirmation - Invoice #{invoice.invoice_number}'
    message = f'''
    Dear {invoice.student.parent.user.get_full_name()},
    
    Your payment has been successfully processed.
    
    Invoice Details:
    - Invoice Number: {invoice.invoice_number}
    - Student: {invoice.student.user.get_full_name()}
    - Amount Paid: ${payment.amount}
    - Payment Date: {payment.payment_date}
    - Payment Reference: {payment.transaction_id}
    
    Thank you for your payment.
    
    Best regards,
    Excel International Academy
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [invoice.student.parent.user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email sending error: {e}")



@login_required
def payment_history(request):
    """View payment history with statistics"""
    parent = request.user.parent
    children = parent.children.all()
    payments = Payment.objects.filter(invoice__student__in=children).order_by('-payment_date')
    
    # Calculate statistics
    total_amount = sum(p.amount for p in payments)
    successful_payments = payments.filter(invoice__status='paid').count()
    pending_payments = payments.filter(invoice__status__in=['pending', 'partial']).count()
    
    context = {
        'payments': payments,
        'total_amount': total_amount,
        'successful_payments': successful_payments,
        'pending_payments': pending_payments,
    }
    return render(request, 'finance/payment_history.html', context)

@csrf_exempt
def verify_paystack_payment(request):
    """Verify Paystack payment (called from JavaScript)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reference = data.get('reference')
            invoice_id = data.get('invoice_id')
            
            if not reference or not invoice_id:
                return JsonResponse({'success': False, 'message': 'Missing parameters'})
            
             # Extract the original reference (remove timestamp suffix)
            original_reference = reference.split('_')[0:-1]  # Remove timestamp part
            original_reference = '_'.join(original_reference)


            # Verify payment with Paystack
            verification = paystack_api.verify_transaction(reference)
            
            if verification.get('status') and verification['data']['status'] == 'success':
                # Payment was successful
                invoice = Invoice.objects.get(id=invoice_id)
                payment_data = verification['data']
                
                # Create payment record
                payment = Payment.objects.create(
                    invoice=invoice,
                    amount=payment_data['amount'] ,  
                    payment_method='paystack',
                    payment_date=timezone.now(),
                    transaction_id=reference,
                    original_reference=original_reference,  
                    receipt_number=f"PAYSTACK_{payment_data['reference']}",
                    paystack_reference=payment_data['reference'],
                    paystack_authorization=payment_data.get('authorization'),
                    confirmed_by=None
                )
                
                # Update invoice status
                if payment.amount >= invoice.amount:
                    invoice.status = 'paid'
                else:
                    invoice.status = 'partial'
                invoice.save()
                
                # Send confirmation email
                send_payment_confirmation(invoice, payment)
                
                return JsonResponse({'success': True, 'message': 'Payment verified successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Payment verification failed'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
