from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .decorators import verified_email_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import login, authenticate
from render_block import render_block_to_string
from django.urls import reverse
from django.db import IntegrityError
from django.http import HttpResponse
from .countries import COUNTRY_CODES
import random
import time


# Create your views here.
@verified_email_required
def home(request):
    xy = ''
    if request.user.is_authenticated:
        xy = 'bread'
    else:
        return redirect('account_login')
    return render(request, 'base.html', {'con': xy})


@verified_email_required
def profile(request, sk):
    profile_obj = Profile.objects.filter(public_id = sk).first()
    context = {
        'profile_obj': profile_obj,
        'country_code': COUNTRY_CODES.get(profile_obj.nationality.lower()),
    }

    if request.htmx:
        if request.POST.get('show_history') == 'true':
            context['show_history'] = True

            html = render_block_to_string('user_profile.html', 'logging_history_block', context, request)
            return HttpResponse(html)

    context['show_history'] = False
    return render(request, 'user_profile.html', context)


def signup(request):
    if request.htmx:
        full_name = request.POST.get('fname')
        email = request.POST.get('email')
        pwd = request.POST.get('pwd')
        nationality = request.POST.get('nationality')
        fav_team = request.POST.get('fav_team')
        reason = request.POST.get('reason')
        username = request.POST.get('username')
        terms = request.POST.get('terms')
        privacy = bool(request.POST.get('privacy'))

        if User.objects.filter(username = username).exists():
            error_msg = 'Username already exists...'
        elif User.objects.filter(email = email).exists():
            error_msg = 'Email already exists...'
        elif not terms:
            error_msg = 'Agree to the terms'
        else:
            try:
                user_obj = User.objects.create_user(username = username, email = email, password = pwd)
                user_profile = Profile.objects.create(
                    full_name = full_name,
                    user = user_obj,
                    fav_team = fav_team,
                    private_acct = privacy,
                    nationality = nationality,
                    reason = reason,
                    # profile_src = random.randint(1, 100)
                )
            
                user = authenticate(request, username = username, password = pwd)
                if user is not None:
                    login(request, user)

                response = HttpResponse()
                response['HX-Redirect'] = reverse('account_email_verification_sent')
                return response
            except Exception as e:
                error_msg = 'An error occurred. Try again'

        response = HttpResponse(error_msg)
        return response
        
    return render(request, 'signup.html')