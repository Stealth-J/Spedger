from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .decorators import verified_email_required
from .helpers import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from render_block import render_block_to_string
from django.urls import reverse
from django.db import IntegrityError
from django.http import HttpResponse
from django.conf import settings
from .countries import COUNTRY_CODES
import random
import time
import re
from datetime import datetime


USERNAME_REGEX = re.compile(r'^(?!.*__)[A-Za-z][A-Za-z0-9_$@!#%&*-]{2,19}$')

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

    if not profile_obj:
        messages.warning(request, 'Profile does not exist')
        return redirect('home')

    if profile_obj.private_acct:
        if request.user != profile_obj.user:
            messages.warning(request, "You cannot view a private account's profile")
            return redirect('home')

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


@verified_email_required
def delete_acct(request, sk):
    profile_obj = Profile.objects.filter(public_id = sk).first()
    if request.user != profile_obj.user:
        messages.warning(request, 'You cannot delete an account that isnt yours.')
        return redirect('profile', sk = sk)
    
    reason = request.POST.get('delete_reason')
    if reason != '':
        DeleteReason.objects.create(reason = reason)

    logout(request)
    profile_obj.user.delete()
    messages.info(request, 'Your account has been deleted and all associated data has been removed')
    return redirect('signup')


@verified_email_required
def settings(request):
    profile_obj = request.user.user_profile
    
    if not profile_obj:
        messages.warning(request, 'An error occurred')
        return redirect('home')
    
    context = {'profile_obj': profile_obj}

    if request.htmx:
        form_error = ''

        if request.POST.get('acct_privacy'):
            block_name = 'private_acct_form_block'
            profile_obj.private_acct = not profile_obj.private_acct
            profile_obj.save()

        elif request.POST.get('slips_reveal'):
            block_name = 'reveal_slip_form_block'
            profile_obj.reveal_slips = not profile_obj.reveal_slips
            profile_obj.save()

        elif request.POST.get('log_all_slips'):
            block_name = 'log_all_slips_form_block'
            profile_obj.log_all_slips = not profile_obj.log_all_slips
            profile_obj.save()

        elif request.POST.get('update_info'):
            username = request.POST.get('username')
            full_name = request.POST.get('full_name')

            if username == '' or full_name == '':
                form_error = 'You cannot submit an empty field'
            elif len(full_name) < 3:
                form_error = 'Full Name must have at least three letters'
            elif not bool(USERNAME_REGEX.match(username)):
                form_error = 'Invalid Username. Pick another one'
            elif User.objects.filter(username = username).exclude(id = request.user.id).exists():
                form_error = 'Username has been taken'
            else:
                form_error = ''
                profile_obj.user.username = username
                profile_obj.full_name = full_name
                profile_obj.user.save()
                profile_obj.save()

                messages.success(request, 'Info updated successfully')
                response = HttpResponse()
                response['HX-Redirect'] = reverse('settings')
                return response
            
            block_name = 'edit_info_form_block'
            context['form_error'] = form_error
            
        else:
            messages.warning(request, 'An error occurred')
            response = HttpResponse()
            response['HX-Redirect'] = reverse('settings')
            return response

        html = render_block_to_string('settings.html', block_name, context, request)
        return HttpResponse(html)

    return render(request, 'settings.html', context)


@verified_email_required
def support(request):
    profile_obj = request.user.user_profile

    if request.htmx:
        try:
            feedback = request.POST.get('feedback')
            subject = 'Feedback submission - Spedger'
            body = f'New feedback has been submitted.\n\nUser:\n- Name: { profile_obj.full_name }\n- Email: { request.user.email }\n- User ID: { request.user.id }\n\n\nMessage:\n------------------\n{ feedback }\n------------------\n\nSubmitted at:\n{datetime.now().strftime("%d %b %y, %H:%M")}\n\nYou can reply directly to this email to reply to the user'

            send_mail(subject, feedback, settings.EMAIL_HOST_USER)
            messages.info(request, "Thanks for reaching out. We'll reach out to you as soon as possible")

        except Exception as e:
            messages.error(request, "An error occurred while sending email.")
            
        response = HttpResponse('')
        response['HX-Trigger'] = 'hx_message_init'
        return response

    return render(request, 'support.html')

def terms(request):
    return render(request, 'terms.html')

def privacy_policy(request):
    return render(request, 'privacy-policy.html')


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
                    reveal_slips = not privacy,
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


def custom_logout(request):
    logout(request)
    return redirect('account_login')


def htmx_messages(request):
    response = render(request, 'partials/messages.html')
    response['HX-Trigger-After-Swap'] = 'hx_message'
    return response