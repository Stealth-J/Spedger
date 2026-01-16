from .views import verified_email_required, total_notifications


def show_notifs(request):
    if not request.user.is_authenticated:
        return {}
    if not request.user.emailaddress_set.filter(verified = True).exists():
        return {}

    requests, duels = total_notifications(request)
    total_notifs = requests + duels
    profile_obj = request.user.user_profile or {}
    user_groups = request.user.user_profile.groups.order_by('-created_on') or {}
    return {
        'total_notifs': total_notifs, 
        'tt_requests': requests, 
        'tt_duels': duels, 
        'profile_obj': profile_obj, 
        'user_groups': user_groups
    }
