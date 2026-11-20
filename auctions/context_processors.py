from .models import Notification

def notifications_processor(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False)
        unread_count = unread_notifications.count()
        latest_notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
        return {
            'unread_notifications_count': unread_count,
            'latest_notifications': latest_notifs,
        }
    return {
        'unread_notifications_count': 0,
        'latest_notifications': [],
    }
