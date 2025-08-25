# core/admin_views.py
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Application, ContactMessage
from notifications.models import Notification
from django.db.models import Q

def is_admin(user):
    return user.user_type == 'admin'

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def application_list(request):
    """List all enrollment applications"""
    applications = Application.objects.all().order_by('-application_date')
    status_filter = request.GET.get('status')
    desired_class_filter = request.GET.get('desired_class')
    search_query = request.GET.get('search')
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    if desired_class_filter:
        applications = applications.filter(desired_class__icontains=desired_class_filter)
    
    if search_query:
        applications = applications.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(child_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    context = {
        'applications': applications,
        'status_filter': status_filter,
        'desired_class_filter': desired_class_filter,
        'search_query': search_query,
    }
    return render(request, 'core/admin/application_list.html', context)
@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        review_notes = request.POST.get('review_notes', '')
        
        application.status = status
        application.review_notes = review_notes
        application.reviewed_by = request.user
        application.review_date = timezone.now()
        application.save()
        
        # Send email notification to applicant
        if status == 'approved':
            email_subject = 'Application Approved - Excel International Academy'
            email_body = f'Dear {application.first_name} {application.last_name},\n\n' \
                        f'We are pleased to inform you that your application for {application.child_name} ' \
                        f'has been approved. Our admissions team will contact you shortly with further instructions ' \
                        f'about the enrollment process.\n\nBest regards,\nExcel International Academy Admissions Team'
        elif status == 'rejected':
            email_subject = 'Application Update - Excel International Academy'
            email_body = f'Dear {application.first_name} {application.last_name},\n\n' \
                        f'After careful review, we regret to inform you that your application for {application.child_name} ' \
                        f'could not be approved at this time. Please contact our admissions office for more information.\n\n' \
                        f'Best regards,\nExcel International Academy Admissions Team'
        else:
            email_subject = 'Application Status Update - Excel International Academy'
            email_body = f'Dear {application.first_name} {application.last_name},\n\n' \
                        f'Your application for {application.child_name} has been updated to: {application.get_status_display()}.' \
                        f'\n\nBest regards,\nExcel International Academy Admissions Team'
        
        send_mail(
            email_subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [application.email],
            fail_silently=False,
        )
        
        messages.success(request, f'Application status updated to {application.get_status_display()}')
        return redirect('application_detail', pk=application.pk)
    
    context = {
        'application': application,
    }
    return render(request, 'core/admin/application_detail.html', context)

@login_required
@user_passes_test(is_admin)
def application_list(request):
    """List all enrollment applications"""
    applications = Application.objects.all().order_by('-application_date')
    status_filter = request.GET.get('status')
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    context = {
        'applications': applications,
        'status_filter': status_filter,
    }
    return render(request, 'core/admin/application_list.html', context)

@login_required
@user_passes_test(is_admin)
def application_detail(request, pk):
    """View and process an individual application"""
    application = get_object_or_404(Application, pk=pk)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        review_notes = request.POST.get('review_notes', '')
        
        application.status = status
        application.review_notes = review_notes
        application.reviewed_by = request.user
        application.review_date = timezone.now()
        application.save()
        
        # Send email notification to applicant
        if status == 'approved':
            email_subject = 'Application Approved - Excel International Academy'
            email_body = f'Dear {application.first_name} {application.last_name},\n\n' \
                        f'We are pleased to inform you that your application for {application.child_name} ' \
                        f'has been approved. Our admissions team will contact you shortly with further instructions ' \
                        f'about the enrollment process.\n\nBest regards,\nExcel International Academy Admissions Team'
        elif status == 'rejected':
            email_subject = 'Application Update - Excel International Academy'
            email_body = f'Dear {application.first_name} {application.last_name},\n\n' \
                        f'After careful review, we regret to inform you that your application for {application.child_name} ' \
                        f'could not be approved at this time. Please contact our admissions office for more information.\n\n' \
                        f'Best regards,\nExcel International Academy Admissions Team'
        else:
            email_subject = 'Application Status Update - Excel International Academy'
            email_body = f'Dear {application.first_name} {application.last_name},\n\n' \
                        f'Your application for {application.child_name} has been updated to: {application.get_status_display()}.' \
                        f'\n\nBest regards,\nExcel International Academy Admissions Team'
        
        send_mail(
            email_subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [application.email],
            fail_silently=False,
        )
        
        messages.success(request, f'Application status updated to {application.get_status_display()}')
        return redirect('application_detail', pk=application.pk)
    
    context = {
        'application': application,
    }
    return render(request, 'core/admin/application_detail.html', context)