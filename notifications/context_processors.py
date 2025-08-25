# notifications/context_processors.py
from django.core.cache import cache
from .models import Notification

def notification_count(request):
    if request.user.is_authenticated:
        # Use cache to avoid hitting the database on every request
        cache_key = f'unread_notifications_{request.user.id}'
        unread_count = cache.get(cache_key)
        
        if unread_count is None:
            unread_count = Notification.objects.filter(
                recipient=request.user, 
                is_read=False
            ).count()
            # Cache for 30 seconds
            cache.set(cache_key, unread_count, 30)
        
        return {
            'unread_notifications_count': unread_count
        }
    return {'unread_notifications_count': 0}