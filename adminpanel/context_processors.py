from staff.models import Notification

def unread_notifications(request):
    if request.user.is_authenticated and request.user.is_superuser:
        all_notifs = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')

        unread_count = all_notifs.filter(is_read=False).count()

        notifications = all_notifs[:10]

        return {
            'unread_count': unread_count,
            'notifications': notifications
        }
    return {'unread_count': 0, 'notifications': []}