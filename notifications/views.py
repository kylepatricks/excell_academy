# notifications/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse

from accounts.models import CustomUser
from .models import Notification

def is_admin(user):
    return user.user_type == 'admin'

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/list.html', context)

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notification_list')

@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notification_list')

@login_required
def notification_count(request):
    """Return the count of unread notifications for the current user"""
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': unread_count})

@login_required
def send_notification(request):
    if request.method == 'POST':
        recipient_type = request.POST.get('recipient_type')
        title = request.POST.get('title')
        message = request.POST.get('message')
        notification_type = request.POST.get('notification_type', 'info')
        related_url = request.POST.get('related_url', '')
        
        if recipient_type == 'all_parents':
            recipients = CustomUser.objects.filter(user_type='parent', is_active=True)
        elif recipient_type == 'all_teachers':
            recipients = CustomUser.objects.filter(user_type='teacher', is_active=True)
        elif recipient_type == 'all_students':
            recipients = CustomUser.objects.filter(user_type='student', is_active=True)
        elif recipient_type == 'specific':
            recipient_ids = request.POST.getlist('recipients')
            recipients = CustomUser.objects.filter(id__in=recipient_ids, is_active=True)
        else:
            recipients = CustomUser.objects.none()
        
        notification_count = 0
        for recipient in recipients:
            Notification.objects.create(
                recipient=recipient,
                title=title,
                message=message,
                notification_type=notification_type,
                related_url=related_url or None
            )
            notification_count += 1
        
        messages.success(request, f'Notification sent to {notification_count} recipients')
        return render(request, 'notifications/send_success.html', {'notification_count': notification_count})
    
    # For GET request, show form
    users = CustomUser.objects.filter(is_active=True).order_by('user_type', 'first_name', 'last_name')
    recent_notifications = Notification.objects.all().order_by('-created_at')[:5]
    
    context = {
        'users': users,
        'recent_notifications': recent_notifications,
    }
    return render(request, 'notifications/send.html', context)