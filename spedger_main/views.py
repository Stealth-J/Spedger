from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .decorators import verified_email_required
from .helpers import *
from django.contrib.auth.decorators import login_required, user_passes_test
from .tasks import *
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from render_block import render_block_to_string
from django.urls import reverse
from django.db import IntegrityError
from django.db.models import ExpressionWrapper, F, Count, Case, FloatField
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q
from .countries import COUNTRY_CODES
from .preview_slip import preview, get_slip_details, save_preview_changes, create_slip_obj, urlparse, filter_wkly_slips, reverse_slip_obj
from .booking import book
import random
import time
import re
import json
from datetime import datetime


USERNAME_REGEX = re.compile(r'^(?!.*__)[A-Za-z][A-Za-z0-9_$@!#%&*-]{2,19}$')

# Create your views here.
@verified_email_required
def home(request):
    try:
        losses = request.user.slips.filter(settled = True, slip_won = False).count()
        events_all = SlipEvent.objects.filter(slip__user = request.user, event_settled = True).count()
        events_won = SlipEvent.objects.filter(slip__user = request.user, event_settled = True, event_won = True).count()
        acc = round((events_won / events_all) * 100)

    except Exception as e:
        if type(e) == ZeroDivisionError:
            losses = 0
            acc = 0
        print(f'Error - {e}')
    return render(request, 'home.html', {'losses': losses, 'accuracy': acc})


@verified_email_required
def profile(request, sk):
    this_profile = Profile.objects.filter(public_id = sk).first()
    all_slips = this_profile.user.slips.order_by('-entry_date')
    if request.user != this_profile.user:
        all_slips = all_slips.exclude(weekly = True)

    all_player_objs = WeeklyGameParticipant.objects.filter(user = request.user, wkly_game__current_game = False).order_by('id')

    if all_player_objs:
        recent_finish = all_player_objs.last().ranking
        highest_finish = all_player_objs.aggregate(result = models.Min('ranking'))['result']
    else:
        recent_finish = 'None'
        highest_finish = 'None'

    slips = paginate(request, all_slips)
    is_viewer = request.user in this_profile.viewers.all()

    if not this_profile:
        messages.warning(request, 'Profile does not exist')
        return redirect('home')

    if this_profile.private_acct:
        if request.user != this_profile.user:
            messages.warning(request, "You cannot view a private account's profile")
            return redirect('home')

    context = {
        'this_profile': this_profile,
        'country_code': COUNTRY_CODES.get(this_profile.nationality.lower()),
        'recent_finish': recent_finish or 'None',
        'highest_finish': highest_finish or 'None',
        'this_slips': slips,
        'from_profile_view': 'yes',
        'is_viewer': request.user in this_profile.viewers.all(),
        'show_slips_codes': (is_viewer and this_profile.reveal_slips) or this_profile.user == request.user
    }

    if request.htmx:
        if request.POST.get('show_history') == 'true':
            context['show_history'] = True

            html = render_block_to_string('user_profile.html', 'logging_history_block', context, request)
            response = HttpResponse(html)
            response['HX-Trigger-After-Swap'] = 'hx_auto_scroll'
            return response

    context['show_history'] = False
    return render(request, 'user_profile.html', context)


@verified_email_required
def load_more_slips_history(request, sk, page_num):
    try:
        this_profile = Profile.objects.filter(public_id = sk).first()
        is_viewer = request.user in this_profile.viewers.all()

        all_slips = this_profile.user.slips.order_by('-entry_date')
        if request.user != this_profile.user:
            all_slips = all_slips.exclude(weekly = True)
        slips = paginate(request, all_slips, page_num)

        context = { 
            'this_profile': this_profile, 
            'this_slips': slips, 
            'from_profile_view': 'no', 
            'is_viewer': is_viewer,
            'show_slips_codes': (is_viewer and this_profile.reveal_slips) or this_profile.user == request.user
        }
        html = render_block_to_string('user_profile.html', 'slips_history_block', context, request)
        response = HttpResponse(html)
        response['HX-Trigger-After-Swap'] = 'hx_auto_scroll'
        return response

    except Exception as e:
        print(f'Error - {e}')
        messages.error(request, 'An Error Occurred')
        response = HttpResponse('')
        response['HX-Trigger'] = 'hx_message_init'
        response['HX-Reswap'] = 'none'
        return response


@verified_email_required
def join_code_viewers(request, sk):
    response = HttpResponse('')
    try:
        this_profile = Profile.objects.filter(public_id = sk).first()
        if this_profile.user == request.user:
            raise Exception('You cannot view your codes by default')
        if this_profile.reveal_slips == False:
            raise Exception("You cannot view this user's slips")
        
        if request.user in this_profile.viewers.all():
            this_profile.viewers.remove(request.user)
            viewing = 'No'
        else:
            this_profile.viewers.add(request.user)
            viewing = 'Yes'
        response = HttpResponse(viewing)

    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, 'An Error Occurred')
        response['HX-Trigger'] = 'hx_message_init'
        response['HX-Reswap'] = 'none'
    
    return response


@verified_email_required
def unfriend_user(request, sk):
    response = HttpResponse('')

    try:
        user_profile_obj = Profile.objects.filter(public_id = sk).first()

        user_profile_obj.friends.remove(request.user)
        request.user.user_profile.friends.remove(user_profile_obj.user)
        messages.info(request, f'{user_profile_obj.user.username} is no longer a friend.')

    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, str(e))

    response['HX-Trigger'] = 'hx_message_init'
    return response


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
    duels = Duel.objects.prefetch_related('duellists').filter(duellists__user = request.user).order_by('-created_at')
    profile_obj = request.user.user_profile
    center_info_msg = 'Search Results appear here'

    total_requests = FriendRequest.objects.select_related('sender', 'recipient')
    sent_requests = total_requests.filter(sender = request.user)
    received_requests = total_requests.filter(recipient = request.user, status = 'open')

    your_duels = duels.exclude(duel_status = 'rejected')
    your_duels = paginate(request, your_duels)
    open_duels = Duel.objects.prefetch_related('duellists').filter(duellists__user = request.user, duel_status = 'open', duellists__recipient = True)

    context = {
        'center_info_msg': center_info_msg,
        'profile_obj': profile_obj,
        'sent_requests': sent_requests,
        'received_requests': received_requests,
        'your_duels': your_duels,
        'open_duels': open_duels,
    }
    return render(request, 'users.html', context)


@verified_email_required
def load_more_duels(request, page_num):
    duels = Duel.objects.prefetch_related('duellists').filter(duellists__user = request.user).exclude(duel_status = 'rejected').order_by('-created_at')
    your_duels = paginate(request, duels, page_num)
    context = {'your_duels': your_duels}
    html = render_block_to_string('users.html', 'duels_block', context, request)
    response = HttpResponse(html)
    return response


@verified_email_required
def filter_duels(request):
    duel_filter = request.POST.get('duel_filter')
    duel_filter2 = request.POST.get('duel_filter2')
    filtered_duels = Duel.objects.prefetch_related('duellists').filter(duellists__user = request.user).order_by('-created_at')
    context = {}
    filters = {
        'duellists__user': request.user,
    }
    exclude_filters = {}

    try:
        if duel_filter == 'rejected':
            filters['duellists__recipient'] = False
            filters['duel_status'] = 'rejected'

        elif duel_filter == 'wins':
            filters['winning_user'] = request.user

        elif duel_filter == 'active':
            filters['settled'] = False
            filters['duel_status'] = 'accepted'
        else:
            exclude_filters['duel_status'] = 'rejected'

        if duel_filter2 == 'sent':
            filters['duellists__recipient'] = False
        elif duel_filter2 == 'received':
            filters['duellists__recipient'] = True

        filtered_duels = Duel.objects.prefetch_related('duellists').filter(**filters).exclude(**exclude_filters).order_by('-created_at')
        context['your_duels'] = filtered_duels

    except Exception as e:
        print(f'Error - {e}')
        messages.error(request, 'An error occurred. Try again')
        response = HttpResponse('')
        response['HX-Reswap'] = 'none'
        response['HX-Trigger'] = 'hx_message_init'
        return response

    html = render_block_to_string('users.html', 'duels_history_block', context, request)
    response = HttpResponse(html)
    return response


@verified_email_required
def search_users(request):
    center_info_msg = 'User not found'
    profile_obj = request.user.user_profile
    keyword = request.POST.get('search_word')
    results = Profile.objects.filter(
        Q(full_name__icontains = keyword) | Q(user__username__icontains = keyword)
    ).exclude(user = request.user).exclude(private_acct = True)[:30]
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
                    request.user.user_profile.friends.add(each.sender)
                    each.sender.user_profile.friends.add(request.user)
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
def my_diary(request):
    center_info_msg = 'Slip preview would appear here'

    if request.htmx:
        if request.POST.get('clear_preview'):
            context = { 'center_info_msg': center_info_msg }
            html = render_block_to_string('my_diary.html', 'preview_display_block', context, request)
            return HttpResponse(html)

    entries = DiaryEntry.objects.filter(user = request.user).order_by('-created_at')
    profile_obj = request.user.user_profile

    context = {
        'entries': entries,
        'last_entry': entries.first(),
        'profile_obj': profile_obj,
        'center_info_msg': center_info_msg,
    }
    return render(request, 'my_diary.html', context)


@verified_email_required
def reload_entries(request, kind):
    entries = DiaryEntry.objects.prefetch_related('user').filter(user = request.user).order_by('-created_at')
    context = {'entries': entries}
    
    if kind == 'replace':
        html = render_block_to_string('my_diary.html', 'entries_block', context, request)
        response = HttpResponse(html)
        response['HX-Trigger-After-Swap'] = json.dumps({'hx_init_components': '', 'hx_close_modal': ''})
        return response


@verified_email_required
def create_entry(request):
    try:
        code = request.POST.get('slip_code').strip()
        success, valid_games = preview(code)
        if not success:
            raise valid_games
        
        slip_info = get_slip_details(valid_games)
        success, code = book(valid_games)
        if not success:
            raise Exception(code)

        entry_obj = create_slip_obj(request, valid_games, slip_info, code, log_in_diary = True)
        preview_result = True

        context = {
            'slip_info': slip_info,
            'slip_code': code,
            'valid_games': valid_games,
            'center_info_msg': ''
        }

    except Exception as e:
        print(f'Error - {e}')
        preview_result = False
        context = { 'error_msg': str(e)}

    html = render_block_to_string('my_diary.html', 'preview_display_block', context, request)
    response = HttpResponse(html)

    if preview_result:
        messages.success(request, 'Entry saved successfully')
        response['HX-Trigger'] = json.dumps({'hx_message_init': '', 'update_entries': entry_obj.id})
        
    return response
    

@verified_email_required
def delete_entries(request, pk):
    entries = DiaryEntry.objects.prefetch_related('user').filter(user = request.user).order_by('-created_at')
    context = {}

    try:
        if pk == 'all':
            entries.delete()
            messages.success(request, 'Entries were deleted successfully.')
            entries_left = DiaryEntry.objects.filter(user = request.user).order_by('-created_at')

            context['entries'] = entries_left
            html = render_block_to_string('my_diary.html', 'entries_block', context, request)
            response = HttpResponse(html)

        elif pk == 'some':
            entry_ids_list = request.POST.get('entry_id')
            entry_ids = entry_ids_list.split(',')
            entry_ids = [ int(entry_id) for entry_id in entry_ids ]
            entries = DiaryEntry.objects.prefetch_related('user').filter(id__in = entry_ids, user = request.user)
            entries.delete()

            entries_left = DiaryEntry.objects.filter(user = request.user).order_by('-created_at')
            if len(entry_ids) == 1 and entries_left.count() > 0:
                messages.success(request, 'Entry deleted successfully')
                response = HttpResponse('')
                response['HX-Retarget'] = f'#entry{entry_ids[0]}'
                response['HX-Reswap'] = 'delete swap:0.4s'
                response['HX-Trigger'] = 'hx_message_init'
                response['HX-Trigger-After-Swap'] = 'hx_close_modal'
                return response
            else:
                messages.success(request, 'Entries deleted successfully.')

            context['entries'] = entries_left
            html = render_block_to_string('my_diary.html', 'entries_block', context, request)
            response = HttpResponse(html)

    except Exception as e:
        print(f'Error - {e}')
        messages.error(request, 'An Error occurred during the process')
        response = HttpResponse('')
        response['HX-Reswap'] = 'none'
        response['HX-Trigger'] = 'hx_message_init'
        response['HX-Trigger-After-Swap'] = 'hx_close_modal'
        return response

    response['HX-Trigger'] = 'hx_message_init'
    response['HX-Trigger-After-Swap'] = json.dumps( {'hx_close_modal': '', 'hx_init_components': ''} )
    return response


@verified_email_required
def filter_entries(request):
    context = {}

    slip_code = request.POST.get('slip_code')
    filter_odds = request.POST.get('filter_odds')
    filter_odds_dir = request.POST.get('filter_odds_dir')
    filter_winpercent = request.POST.get('filter_winpercent')
    filter_winpercent_dir = request.POST.get('filter_winpercent_dir')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    wins_cb = request.POST.get('wins_cb')

    filters = {'user': request.user}
    annotate_filters = {}

    try:
        if slip_code:
            filters['slip__slip_code__icontains'] = slip_code
        if filter_odds:
            filters[f'slip__total_odds__{filter_odds_dir}'] = filter_odds
        if filter_winpercent:
            annotate_filters['total_events'] = Count('slip__slip_events')
            annotate_filters['events_won'] = Count('slip__slip_events', filter = Q(slip__slip_events__event_won = True))
            annotate_filters['win_percentage'] = Case(
                default = F('events_won') * 100.0 / F('total_events'), 
                output_field = FloatField()
            )
            filters[f'win_percentage__{filter_winpercent_dir}'] = filter_winpercent
        if start_date:
            filters['created_at__gte'] = start_date
        if end_date:
            filters['created_at__lte'] = end_date
        if wins_cb == 'wins':
            filters['slip__slip_won'] = True

        entries = DiaryEntry.objects.annotate(**annotate_filters).filter(**filters).order_by('-created_at')
        context['entries'] = entries
        html = render_block_to_string('my_diary.html', 'entries_block', context, request)
        response = HttpResponse(html)
        response['HX-Trigger-After-Swap'] = json.dumps( {'hx_close_modal': '', 'hx_init_components': ''} )

    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, 'Oops. An Error Occurred')
        response = HttpResponse('')
        response['HX-Reswap'] = 'none'
        response['HX-Trigger'] = 'hx_message_init'
        response['HX-Trigger-After-Swap'] = 'hx_close_modal'
        
    return response


@verified_email_required
def leaderboards_view(request):
    center_info_msg = 'Slip preview would appear here'
    all_games = WeeklyGame.objects.prefetch_related('game_participants', 'game_participants__slip').order_by('id')
    all_player_objs = WeeklyGameParticipant.objects.filter(user = request.user, wkly_game__current_game = False).order_by('id')

    current_wkly_game = all_games.filter(current_game = True).first()
    if all_player_objs:
        player_obj = current_wkly_game.game_participants.filter(user = request.user).first()
        is_current_player = bool(player_obj)
    else:
        player_obj = None
        is_current_player = False
    valid_games = []
    slip_info = {}

    try:
        wkly_board = rank_users_leaderboards(current_wkly_game.game_participants.all())
        global_board = rank_users_leaderboards(wkly = False)
        previous_obj = all_player_objs.last()

        if is_current_player:
            valid_games = reverse_slip_obj(player_obj.slip)
            slip_info = get_slip_details(valid_games)
            for each in list(wkly_board):
                if each.user == request.user:
                    player_obj = each
                    break
        
        context = {
            'center_info_msg': center_info_msg,
            'current_wkly_game': current_wkly_game,
            'is_current_player': is_current_player,
            'valid_games': valid_games,
            'slip_info': slip_info,
            'player_obj': player_obj,
            'previous_obj': previous_obj,
            'wkly_users': wkly_board[:30],
            'global_users': global_board[:30],
        }
    
    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, 'Something unexpected happened')
        context = {
            'center_info_msg': center_info_msg,
            'current_wkly_game': [],
            'is_current_player': False,
            'valid_games': [],
            'slip_info': None,
            'player_obj': None,
            'previous_obj': None,
            'wkly_users': [],
            'global_users': [],
        }

    return render(request, 'leaderboards.html', context) 


@verified_email_required
def register_wkly_game(request):
    context = {}
    preview_result = False
    try:
        current_wkly_game = WeeklyGame.objects.filter(current_game = True).first()
        if not current_wkly_game:
            raise Exception('There is no weekly game yet')
        elif current_wkly_game.game_participants.filter(user = request.user).exists():
            raise Exception("You have already registered for this game week")

        code = request.POST.get('slip_code').strip()
        success, valid_games = preview(code)
        if not success:
            raise valid_games
        
        valid_games = filter_wkly_slips(d_games, current_wkly_game)
        slip_info = get_slip_details(valid_games)
        success, code = book(valid_games)
        if not success:
            raise Exception(code)

        slip_obj = create_slip_obj(request, valid_games, slip_info, code, wkly = True)
        participant_obj = WeeklyGameParticipant.objects.create(user = request.user, wkly_game = current_wkly_game, slip = slip_obj)
        preview_result = True

        context = {
            'slip_info': slip_info,
            'slip_code': code,
            'valid_games': valid_games,
            'center_info_msg': ''
        }

    except Exception as e:
        print(f'Error - {e}')
        context = { 'error_msg': str(e) }

    html = render_block_to_string('leaderboards.html', 'preview_display_block', context, request)
    response = HttpResponse(html)

    if preview_result:
        messages.success(request, "You have registered successfully for this week's game")
        response['HX-Trigger'] = 'hx_message_init'

    return response


def reload_leaderboards(request, board):
    if not request.user.is_authenticated:
        response = HttpResponse()
        response['HX-Redirect'] = reverse('account_login')
        return response
    
    current_wkly_game = WeeklyGame.objects.prefetch_related('game_participants', 'game_participants__slip').filter(current_game = True).first()

    try:
        if board == 'wk':
            player_obj = current_wkly_game.game_participants.filter(user = request.user).first()
            is_current_player = bool(player_obj)
            wkly_board = rank_users_leaderboards(current_wkly_game.game_participants.all())

            if is_current_player:
                valid_games = reverse_slip_obj(player_obj.slip)
                player_obj = wkly_board.filter(user = request.user).first()
        
            context = {
                'current_wkly_game': current_wkly_game,
                'is_current_player': is_current_player,
                'player_obj': player_obj,
                'wkly_users': wkly_board[:30],
            }

            html = render_block_to_string('leaderboards.html', 'wkly_boards_block', context, request)
            response = HttpResponse(html)
            response['HX-Trigger-After-Swap'] = 'hx_init_components'
            return response
        
        else:
            global_board = rank_users_leaderboards(wkly = False)
            context = {'global_users': global_board[:30]}

            html = render_block_to_string('leaderboards.html', 'global_boards_block', context, request)
            response = HttpResponse(html)
            return response

    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, 'An Error Occurred')
        response = HttpResponse('')
        response['HX-Reswap'] = 'none'
        response['HX-Trigger'] = 'hx_message_init'
        return response


@verified_email_required
def create_weekly_game(request):
    try:
        if not request.user.is_staff:
            raise Exception('You are not a staff member')
        
        current_game = WeeklyGame.objects.filter(current_game = True).first()
        from_ = datetime.fromisoformat( request.POST.get('from_date_val') )
        to_ = datetime.fromisoformat( request.POST.get('to_date_val') )
        WeeklyGame.objects.create(
            start_date = dj_tz.make_aware(from_), 
            end_date = dj_tz.make_aware(to_)
        )
        current_game.current_game = False
        current_game.save()
        update_players_ranks.delay()

    except Exception as e:
        messages.warning(request, str(e))

    return redirect('leaderboards')


@verified_email_required
def groups(request):
    return render(request, 'groups.html')


@verified_email_required
def group_details(request, sk):
    profile_obj = request.user.user_profile
    muted_ids = profile_obj.muted_users.values_list('id', flat = True)

    try:
        group_obj = GroupChat.objects.filter(group_id = sk).first()
        chat_msgs = group_obj.group_chat_msgs.exclude(user__id__in = muted_ids).order_by('-created_at')
        chat_msgs = paginate(request, chat_msgs)

        ranked_qs = rank_group_members(group_obj.group_members.all())
        is_member = True
        is_leader = group_obj.group_leader == request.user

        if profile_obj.user in group_obj.banned_users.all():
            messages.error(request, f'You have been banned from {group_obj.group_name}')
            return redirect('groups')
        if not profile_obj in group_obj.group_members.all():
            is_member = False
            if group_obj.private_group:
                messages.warning(request, 'You cannot access a private group without being a member')
                return redirect('groups')

        print(ranked_qs)
        for each in ranked_qs:
            print( each.pure_odds_temp )
        context = {
            'group': group_obj,
            'is_member': is_member,
            'is_leader': is_leader,
            'chat_msgs': chat_msgs,
            'ranked_qs': ranked_qs,
        }

    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, 'Something unexpected happened. Try again')
        return redirect('groups')
    
    return render(request, 'group_details.html', context)


@verified_email_required
def load_more_chats(request, sk, page_num):
    profile_obj = request.user.user_profile
    muted_ids = profile_obj.muted_users.values_list('id', flat = True)

    try:
        group_obj = GroupChat.objects.filter(group_id = sk).first()
        if request.user in group_obj.banned_users.all():
            response = HttpResponse('')
            response['HX-Redirect'] = reverse('groups')
            messages.error(request, f'You have been banned from {group_obj.group_name}')
            return response

        all_chat_msgs = group_obj.group_chat_msgs.exclude(user__id__in = muted_ids ).order_by('-created_at')
        chat_msgs = paginate(request, all_chat_msgs, page_num)
        context = { 'chat_msgs': chat_msgs, 'group': group_obj }
        html = render_block_to_string('group_details.html', 'group_chat_msgs_block', context, request)
        response = HttpResponse(html)
        response['HX-Trigger-After-Swap'] = 'hx_init_components'

    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, 'An Error Occurred')
        response = HttpResponse('')
        response['HX-Reswap'] = 'none'
        response['HX-Trigger'] = 'hx_message_init'

    return response


@verified_email_required
def mute_user(request, pk):
    try:
        profile_obj = request.user.user_profile
        user_obj = User.objects.filter(id = pk).first()
        if user_obj == request.user:
            raise Exception('You cannot mute yourself')

        if user_obj in profile_obj.muted_users.all():
            profile_obj.muted_users.remove(user_obj)
        else:
            profile_obj.muted_users.add(user_obj)    
        messages.success(request, 'Reload page to save changes')

    except Exception as e:
        print(f'Error - {e}')
        messages.error(request, str(e))

    response = HttpResponse('')
    response['HX-Trigger'] = 'hx_message_init'
    return response



def group_join(request, sk):
    profile_obj = request.user.user_profile or ''
    try:
        group_obj = GroupChat.objects.filter(group_id = sk).first()
        if not group_obj:
            raise Exception('URL is invalid')
        if profile_obj.user in group_obj.banned_users.all():
            raise Exception(f'You have been banned from {group_obj.group_name}')
        if profile_obj in group_obj.group_members.all():
            return redirect('group_details', sk = sk)
        
        profile_obj.groups.add(group_obj)
        messages.success(request, f'You are now a member of {group_obj.group_name}')

    except Exception as e:
        if not 'banned' in str(e):
            messages.error(request, str(e))

    return redirect('group_details', sk = sk)


def group_join_url(request):
    url_path = request.POST.get('group_url')

    try:
        parsed = urlparse(url_path).path
        sk = parsed.removeprefix('/group-')
        try:
            uuid.UUID(sk)
        except Exception as e:
            raise Exception('URL is invalid')
        
        return redirect('group_join', sk = sk)
    
    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, str(e))
        return redirect('groups')


@verified_email_required
def group_create(request):
    try:
        group_name = request.POST.get('group_name')
        private = bool(request.POST.get('private_group'))
        leader_talk_only = bool(request.POST.get('leader_only'))
        group_obj = GroupChat.objects.create(group_name = group_name, group_leader = request.user, private_group = private, leader_talk_only = leader_talk_only)
        request.user.user_profile.groups.add(group_obj)

    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, 'An Error Occurred.')

    return redirect('groups')


@verified_email_required
def place_admin(request, sk):
    group_obj = GroupChat.objects.filter(group_id = sk).first()
    group_obj.group_leader = request.user
    group_obj.save()
    return redirect('group_details', sk = sk)


@verified_email_required
def group_edit(request, sk):
    profile_obj = request.user.user_profile

    try:
        group_obj = GroupChat.objects.filter(group_id = sk).first()
        
        if not profile_obj in group_obj.group_members.all():
            raise Exception('You are not a member of this group')
        if request.user != group_obj.group_leader:
            raise Exception('Only the group leader can make changes to the group')

        group_name = request.POST.get('group_name')
        private = bool(request.POST.get('private_group'))
        leader_talk_only = bool(request.POST.get('leader_only'))

        group_obj.group_name = group_name
        group_obj.private_group = private
        group_obj.leader_talk_only = leader_talk_only
        group_obj.save()
        
    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, 'An Error Occurred')

    return redirect('group_details', sk = sk)


@verified_email_required
def leave_group(request, sk):
    profile_obj = request.user.user_profile
    group_obj = GroupChat.objects.filter(group_id = sk).first()
    response = HttpResponse('')

    try:
        if not profile_obj in group_obj.group_members.all():
            raise Exception('You are not a member of this group')
        
        if request.user == group_obj.group_leader:
            group_obj.group_leader = None
            group_obj.private_group = False
            group_obj.leader_talk_only = False
            group_obj.save()
        profile_obj.groups.remove(group_obj)

        if request.POST.get('redirect_page') == 'yes':
            return redirect('groups')
        
    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, str(e))
        response['HX-Reswap'] = 'none'
        response['HX-Trigger'] = 'hx_message_init'
    
    return response


@verified_email_required
def remove_from_group(request, user_id, sk):
    profile_obj = request.user.user_profile
    response = HttpResponse('')
    ban = request.POST.get('ban_user')

    try:
        group_obj = GroupChat.objects.filter(group_id = sk).first()
        user_obj = Profile.objects.filter(public_id = user_id).first()

        if not profile_obj in group_obj.group_members.all():
            raise Exception('User is not a member of this group')
        if request.user != group_obj.group_leader:
            raise Exception('Only the group leader can perform this action')
        
        user_obj.groups.remove(group_obj)
        if ban == 'True':
            group_obj.banned_users.add(user_obj.user)
        
    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, str(e))
        response['HX-Reswap'] = 'none'
        response['HX-Trigger'] = 'hx_message_init'
    
    return response


@verified_email_required
def delete_group(request):
    profile_obj = request.user.user_profile
    group_id = request.POST.get('group_id')
    group_obj = GroupChat.objects.filter(group_id = group_id).first()
    response = HttpResponse('')

    try:
        if not profile_obj in group_obj.group_members.all():
            raise Exception('You are not a member of this group')
        if request.user != group_obj.group_leader:
            raise Exception('Only the group leader can delete this group')
        
        group_obj.delete()
        response['HX-Trigger'] = 'hx_close_modal'
        if request.POST.get('redirect_page') == 'yes':
            return redirect('groups')
        
    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, str(e))
        response['HX-Reswap'] = 'none'
        response['HX-Trigger'] = 'hx_message_init'
    
    return response


@verified_email_required
def send_chat(request, sk):
    try:
        group_obj = GroupChat.objects.filter(group_id = sk).first()
        if group_obj.leader_talk_only == True and group_obj.group_leader != request.user:
            raise Exception('Only the leader can send codes')
        if not request.user.user_profile in group_obj.group_members.all():
            raise Exception('Only members can send codes')

        slip_code = request.POST.get('slip_code').strip()
        success, valid_games = preview(slip_code)
        if not success:
            raise valid_games
        
        slip_info = get_slip_details(valid_games)
        slip_obj = create_slip_obj(request, valid_games, slip_info, slip_code)
        chat_msg_obj = GroupChatMsgs.objects.create(user = request.user, slip = slip_obj, group_chat = group_obj)

        context = { 'msg': chat_msg_obj, 'group': group_obj }
        response = render(request, 'partials/group_chat_message.html', context)
        response['HX-Trigger-After-Swap'] = json.dumps({'hx_init_components': '', 'hx_auto_scroll': ''})
        
    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, str(e))
        response = HttpResponse('')
        response['HX-Reswap'] = 'none'
        response['HX-Trigger'] = 'hx_message_init'

    return response


@verified_email_required
def delete_chat(request, sk, msg_id):
    response = HttpResponse('')

    try:
        group_obj = GroupChat.objects.filter(group_id = sk).first()
        msg_obj = GroupChatMsgs.objects.filter(group_chat = group_obj, id = msg_id).first()

        if not request.user.user_profile in group_obj.group_members.all():
            raise Exception('Only members of the group can delete codes')
        
        if request.user == msg_obj.user or request.user == group_obj.group_leader:
            msg_obj.delete()
            messages.success(request, 'Code deleted successfully')
            response['HX-Trigger-After-Swap'] = 'hx_init_components'

        else:
            raise Exception('You are not qualified to delete the code')

    except Exception as e:
        print(f'Error - {str(e)}')
        messages.error(request, 'An Error Cccurred. Try again later')
        response['HX-Reswap'] = 'none'

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
        slip_code = request.session.get('slip_code') or request.POST.get('slip_code')

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

    context = {}

    try:
        success, valid_games = preview(code)
        if not success:
            raise valid_games
        elif not recipient_obj:
            raise Exception('No user found')
        elif minimum_odds:
            total_odds = get_slip_details(valid_games).total_odds
            if float(total_odds) < minimum_odds:
                raise Exception(f"Total odds ({total_odds}) is below {minimum_odds}")    
        
        if not request.user in recipient_obj.user_profile.friends.all():
            raise Exception('You can only duel friends')
        else:
            slip_obj = create_slip_obj( request, valid_games, get_slip_details(valid_games), code)

            duel_obj = Duel.objects.create(minimum_odds = minimum_odds)
            challenger_obj = DuellistInfo.objects.create(slip = slip_obj, duel_obj = duel_obj, user = request.user)
            recipient_obj = DuellistInfo.objects.create(duel_obj = duel_obj, recipient = True, user = recipient_obj)

            context['duel'] = duel_obj
            response = render(request, 'partials/duel.html', context)
            messages.success(request, 'Duel request was sent successfully')
            response['HX-Retarget'] = '.duel'
            response['HX-Reswap'] = 'beforebegin'
            response['HX-Trigger-After-Swap'] = 'hx_close_modal'
            response['HX-Trigger'] = 'hx_message_init'
        
    except Exception as e:
        print(f'Error - {e}')
        context['form_error'] = str(e)
        html = render_block_to_string('users.html', 'form_error_block2', context, request)
        response = HttpResponse(html)

    return response


def accept_duel(request):
    code = request.POST.get('slip_code')
    duel_id = request.POST.get('duel_id')
    duel_obj = Duel.objects.filter(id = duel_id).first()
    duellist_obj = duel_obj.duellists.filter(recipient = True, user = request.user).first()
    challenger_obj = duel_obj.duellists.filter(recipient = False).first()
    context = {}

    try:
        success, valid_games = preview(code)

        if not success:
            raise valid_games
        elif duellist_obj.slip:
            raise Exception('You cannot update your slip')
        elif len(valid_games) < 1:
            raise Exception('No valid selection found')
        elif not duel_obj or not duellist_obj:
            raise Exception('Duel doesnt exist')
        elif duel_obj.minimum_odds:
            total_odds = get_slip_details(valid_games).total_odds
            if float(total_odds) < duel_obj.minimum_odds:
                raise Exception(f"Total odds ({total_odds}) is below the minimum ({duel_obj.minimum_odds})")    
        
        if not request.user in challenger_obj.user.user_profile.friends.all():
            raise Exception('You can only duel friends')
        else:
            slip_obj = create_slip_obj( request, valid_games, get_slip_details(valid_games), code)

            duel_obj.duel_status = 'accepted'
            duellist_obj.slip = slip_obj
            duel_obj.save()
            duellist_obj.save()

            context['duel'] = duel_obj
            response = render(request, 'partials/duel.html', context)
            response['HX-Retarget'] = f'#duel{ duel_id }'
            response['HX-Trigger-After-Swap'] = 'hx_close_modal'
        
    except Exception as e:
        print(f'Error - {e}')
        context['form_error'] = str(e)
        html = render_block_to_string('users.html', 'form_error_block', context, request)
        response = HttpResponse(html)

    return response


def reject_duel(request):
    duel_id = request.POST.get('duel')
    duel_obj = Duel.objects.filter(id = duel_id).first()
    challenger_obj = duel_obj.duellists.filter(recipient = False).first()
    context = {}

    try:
        if not duel_obj:
            raise Exception('Duel doesnt exist')
        elif not request.user in challenger_obj.user.user_profile.friends.all():
            raise Exception('You can only duel friends')

        duel_obj.duel_status = 'rejected'
        duel_obj.save()
        context['duel'] = duel_obj
        response = render(request, 'partials/duel.html', context)
        
    except Exception as e:
        print(f'Error - {e}')
        messages.error(request, 'An error occurred')
        response = HttpResponse('')
        response['HX-Trigger'] = 'hx_message_init'

    return response


def insights(request):
    context = {}
    return render(request, 'insights.html', context)



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
                    profile_img = avatar_img_func(),
                    background_img = background_img_func()
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