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
from django.db.models import Q
from .countries import COUNTRY_CODES
from .preview_slip import preview, get_slip_details, save_preview_changes, create_slip_obj
from .booking import book
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
def account_settings(request):
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
def users(request):
    profile_obj = request.user.user_profile
    center_info_msg = 'Search Results appear here'
    total_requests = FriendRequest.objects.select_related('sender', 'recipient')
    sent_requests = total_requests.filter(sender = request.user)
    received_requests = total_requests.filter(recipient = request.user, status = 'open')
    your_duels = Duel.objects.prefetch_related('duellists').filter(duellists__slip__user = request.user)

    context = {
        'center_info_msg': center_info_msg,
        'profile_obj': profile_obj,
        'sent_requests': sent_requests,
        'received_requests': received_requests,
        'your_duels': your_duels,
    }
    return render(request, 'users.html', context)


@verified_email_required
def search_users(request):
    center_info_msg = 'User not found'
    profile_obj = request.user.user_profile
    keyword = request.POST.get('search_word')
    results = Profile.objects.filter(
        Q(full_name__icontains = keyword) | Q(user__username__icontains = keyword)
    ).exclude(user = request.user)

    context = { 
        'user_results': results, 
        'center_info_msg': center_info_msg,
        'profile_obj': profile_obj,
    }
    html = render_block_to_string('users.html', 'search_results_block', context, request)
    return HttpResponse(html)


@verified_email_required
def send_friend_request(request, sk):
    profile_obj = request.user.user_profile
    recipient_obj = Profile.objects.filter(public_id = sk).first().user
    try:
        if recipient_obj in profile_obj.friends.all():
            messages.warning(request, f'{recipient_obj.username} is a friend already.')

        else:
            existing_request = FriendRequest.objects.filter(sender = profile_obj.user, recipient = recipient_obj, status = 'open')
            existing_received_request = FriendRequest.objects.filter(sender = recipient_obj, recipient = request.user, status = 'open')

            if existing_request.exists():
                messages.warning(request, f'You have already sent {recipient_obj.username} a request')
            else:
                if request.user == recipient_obj:
                    messages.error(request, 'You cannot send a request to yourself')
                elif existing_received_request.exists():
                    messages.warning(request, 'You have a pending request from this user.')
                    
                else:
                    FriendRequest.objects.create(
                        sender = profile_obj.user,
                        recipient = recipient_obj
                    )
                    messages.info(request, f'{recipient_obj.username} was sent a request.')

    except Exception as e:
        print(e)
        messages.error(request, 'Something unexpected happened.')

    response = HttpResponse('')
    response['HX-Trigger'] = 'hx_message_init'
    return response


@verified_email_required
def accept_request(request, pk):
    try:
        if pk == 'all':
            all_requests = FriendRequest.objects.filter(recipient = request.user, status = "open")
            all_requests_list = []
            response = HttpResponse('')

            if all_requests.exists():
                for each in all_requests:
                    each.status = 'accepted'
                    all_requests_list.append(each)
                
                FriendRequest.objects.bulk_update(all_requests_list, ['status'])
                messages.info(request, 'All requests have been accepted')
                response['HX-Redirect'] = 'users'
            else:
                messages.warning(request, 'There are no requests to accept')
                response['HX-Trigger'] = 'hx_message_init'

            return response
        else:
            request_obj = FriendRequest.objects.filter(id = pk).first()
            request_obj.status = 'accepted'
            request_obj.save()
            request.user.user_profile.friends.add(request_obj.sender)
            request_obj.sender.user_profile.friends.add(request.user)
            
            messages.success(request, f'{request_obj.sender.username} is now a friend.')

    except Exception as e:
        print(e)
        messages.error(request, 'Request could not be completed because an error occurred')

    response = HttpResponse('')
    response['HX-Trigger'] = 'hx_message_init'
    return response


@verified_email_required
def reject_request(request, pk):
    try:
        if pk == 'all':
            all_requests = FriendRequest.objects.filter(recipient = request.user, status = 'open')
            all_requests_list = []
            response = HttpResponse('')

            if all_requests.exists():
                for each in all_requests:
                    each.status = 'rejected'
                    all_requests_list.append(each)
                
                FriendRequest.objects.bulk_update(all_requests_list, ['status'])
                messages.info(request, 'All requests have been rejected')
                response['HX-Redirect'] = 'users'
            else:
                messages.warning(request, 'There are no requests to reject')
                response['HX-Trigger'] = 'hx_message_init'

            return response
        else:
            request_obj = FriendRequest.objects.filter(id = pk).first()
            request_obj.status = 'rejected'
            request_obj.save()
            return HttpResponse('')

    except Exception as e:
        print(e)
        messages.error(request, 'Request could not be completed because an error occurred')

    response = HttpResponse('')
    response['HX-Trigger'] = 'hx_message_init'
    return response


@verified_email_required
def delete_request(request, pk):
    try:
        if pk == 'all':
            all_requests = FriendRequest.objects.filter(sender = request.user)
            response = HttpResponse('')

            if all_requests.exists():
                all_requests.delete()
                messages.info(request, 'All requests have been deleted')
                response['HX-Redirect'] = 'users'
            else:
                messages.warning(request, 'There are no requests to delete')
                response['HX-Trigger'] = 'hx_message_init'

            return response
        else:
            request_obj = FriendRequest.objects.filter(id = pk).first()
            request_obj.delete()
            messages.success(request, 'Request deleted successfully')

    except Exception as e:
        print(e)
        messages.error(request, 'Request could not be deleted because an error occurred')

    response = HttpResponse('')
    response['HX-Trigger'] = 'hx_message_init'
    return response


@verified_email_required
def support(request):
    profile_obj = request.user.user_profile

    if request.htmx:
        try:
            feedback = request.POST.get('feedback')
            subject = 'Feedback submission - Spedger'
            body = f'New feedback has been submitted.\n\nUser:\n- Name: { profile_obj.full_name }\n- Email: { request.user.email }\n- User ID: { request.user.id }\n\n\nMessage:\n------------------\n{ feedback }\n------------------\n\nSubmitted at:\n{datetime.now().strftime("%d %b %y, %H:%M")}\n\nYou can reply directly to this email to reply to the user'

            send_mail(subject, body, settings.EMAIL_HOST_USER)
            Feedback.objects.create(user = request.user, message = feedback)
            messages.info(request, "Thanks for reaching out. We'll reach out to you as soon as possible")

        except Exception as e:
            print(e)
            messages.error(request, "An error occurred while sending email.")
            
        response = HttpResponse('')
        response['HX-Trigger'] = 'hx_message_init'
        return response

    return render(request, 'support.html')

def terms(request):
    return render(request, 'terms.html')

def privacy_policy(request):
    return render(request, 'privacy-policy.html')


def preview_slip(request):
    center_info_msg = 'Slip preview would appear here'
    request.session.pop('valid_games', None)
    context = {'center_info_msg': center_info_msg}

    if request.htmx:
        try:
            code = request.POST.get('slip_code').strip()
            success, valid_games = preview(code)
            if not success:
                raise valid_games
            if len(valid_games) < 1:
                raise Exception('No valid selection found')
            
            preview_result = True
            slip_info = get_slip_details(valid_games)
            request.session['valid_games'] = slip_info.valid_games_raw
            request.session['slip_code'] = code

            context = {
                'slip_info': slip_info,
                'slip_code': code,
                'valid_games': valid_games,
                'center_info_msg': ''
            }

        except Exception as e:
            print(f'Error - {e}')
            preview_result = False
            # raise e
            context = { 'error_msg': str(e)}

        html = render_block_to_string('preview.html', 'preview_display_block', context, request)
        response = HttpResponse(html)

        if preview_result:
            response['HX-Trigger-After-Swap'] = 'preview_success'

        return response
    
    return render(request, 'preview.html', context)


def make_preview_changes(request):
    context = {}
    msg = ''

    try:
        removed_ids = request.POST.get('removed_ids')
        valid_games = request.session.get('valid_games')
        slip_code = request.session.get('slip_code')

        if not valid_games:
            raise Exception('An Error occurred. Input the code and try again')
        
        valid_games_left = save_preview_changes(valid_games, removed_ids)
        slip_info = get_slip_details(valid_games_left)
        preview_result = True
        
        if removed_ids == '':
            msg = 'There are no changes to be made'
        else:
            success, slip_code = book(valid_games_left)
            if not success:
                raise Exception(slip_code)

            request.session['slip_code'] = slip_code
            request.session['valid_games'] = slip_info.valid_games_raw

        context = {
            'slip_info': slip_info,
            'slip_code': slip_code,
            'valid_games': valid_games_left,
            'center_info_msg': ''
        }
        
    except Exception as e:
        print(f'Error - {e}')
        preview_result = False
        # raise e
        context = { 'error_msg': str(e)}

    html = render_block_to_string('preview.html', 'preview_display_block', context, request)
    response = HttpResponse(html)

    if preview_result:
        response['HX-Trigger-After-Swap'] = 'preview_success'
    if msg != '':
        messages.info(request, msg)
        response['HX-Trigger'] = 'hx_message_init'

    return response


def send_duel_request(request):
    code = request.POST.get('slip_code')
    recipient_id = request.POST.get('recipient')
    minimum_odds = request.POST.get('minimum_odds') or None
    if minimum_odds: 
        minimum_odds = float(minimum_odds)
    recipient_obj = User.objects.filter(id = recipient_id).first()

    try:
        success, valid_games = preview(code)
        if not success:
            raise valid_games
        elif len(valid_games) < 1:
            raise Exception('No valid selection found')
        elif not recipient_obj:
            raise Exception('No user found')
        
        if not request.user in recipient_obj.user_profile.friends.all():
            raise Exception('You can only duel friends')
        else:
            slip_obj = create_slip_obj( request, valid_games, get_slip_details(valid_games), code)

            duel_obj = Duel.objects.create(minimum_odds = minimum_odds)
            challenger_obj = DuellistInfo.objects.create(slip = slip_obj, duel_obj = duel_obj)
            recipient_obj = DuellistInfo.objects.create(duel_obj = duel_obj, recipient = True)
            messages.success(request, 'Duel request was sent successfully')
        
    except Exception as e:
        print(f'Error - {e}')
        messages.error(request, str(e))

    response = HttpResponse("")
    response['HX-Trigger'] = 'hx_message_init'
    return response


def accept_duel(request):
    pass


def reject_duel(request):
    pass



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