from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def verified_email_required(func):

    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        
        if not request.user.emailaddress_set.filter(verified = True).exists():
            messages.warning(request, 'You need to verify your email to continue.')
            return redirect('account_email_verification_sent')
        
        return func(request, *args, **kwargs)
    return wrapper