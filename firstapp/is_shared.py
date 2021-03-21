from .models import Share

def get_share(from_user, to_user):
    try:
        return Share.objects.get(from_user=from_user, to_user=to_user)
    except Share.DoesNotExist:
        return False
