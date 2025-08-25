# core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from accounts.models import CustomUser
from .models import Facility, Application, ContactMessage
from notifications.models import Notification

def home(request):
    facilities = Facility.objects.filter(is_active=True)[:3]
    return render(request, 'core/index.html', {'facilities': facilities})

def facilities_list(request):
    facilities = Facility.objects.filter(is_active=True)
    return render(request, 'core/facilities.html', {'facilities': facilities})

def apply(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        child_name = request.POST.get('child_name')
        child_age = request.POST.get('child_age')
        desired_class = request.POST.get('desired_class')
        notes = request.POST.get('notes', '')
        
        # Create application
        application = Application.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            child_name=child_name,
            child_age=child_age,
            desired_class=desired_class,
            notes=notes
        )
        
        # Send confirmation email
        send_mail(
            'Application Received - Excel International Academy',
            f'Dear {first_name} {last_name},\n\nThank you for applying to Excel International Academy. '
            f'We have received your application for {child_name} to join {desired_class}. '
            'Our admissions team will review your application and contact you within 3-5 business days.\n\n'
            'Best regards,\nExcel International Academy Admissions Team',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        # Create notification for admin
        admin_users = CustomUser.objects.filter(user_type='admin', is_active=True)
        for admin in admin_users:
            Notification.objects.create(
                recipient=admin,
                title='New Application Received',
                message=f'A new application has been submitted by {first_name} {last_name} for {child_name}',
                notification_type='info',
                related_url=f'/admin/applications/{application.id}/'
            )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Application submitted successfully!'})
        
        messages.success(request, 'Application submitted successfully!')
        return redirect('home')
    
    return render(request, 'core/apply.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Save contact message
        contact_message = ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        
        # Send confirmation email
        send_mail(
            'Message Received - Excel International Academy',
            f'Dear {name},\n\nThank you for contacting Excel International Academy. '
            'We have received your message and will respond to you as soon as possible.\n\n'
            'Best regards,\nExcel International Academy Team',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        # Create notification for admin
        admin_users = CustomUser.objects.filter(user_type='admin', is_active=True)
        for admin in admin_users:
            Notification.objects.create(
                recipient=admin,
                title='New Contact Message',
                message=f'A new message has been received from {name} regarding {subject}',
                notification_type='info',
                related_url=f'/admin/contact-messages/{contact_message.id}/'
            )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Message sent successfully!'})
        
        messages.success(request, 'Message sent successfully!')
        return redirect('home')
    
    return render(request, 'core/contact.html')