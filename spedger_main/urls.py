from django.urls import path
from .views import *

urlpatterns = [
    path('home', home, name = "home"),
    path('signup', signup, name = "signup"),
    path('profile/<str:sk>', profile, name = "profile"),
    path('load_more_slips_history/<str:sk>/<int:page_num>', load_more_slips_history, name = "load_more_slips_history"),
    path('join_code_viewers/<str:sk>', join_code_viewers, name = "join_code_viewers"),
    path('delete_acct/<str:sk>', delete_acct, name = "delete_acct"),
    path('settings', account_settings, name = "settings"),
    path('users', users, name = "users"),
    path('search_users', search_users, name = "search_users"),
    path('filter_duels', filter_duels, name = "filter_duels"),

    path('send_friend_request/<str:sk>', send_friend_request, name = "send_friend_request"),
    path('unfriend_user/<str:sk>', unfriend_user, name = "unfriend_user"),
    path('accept_request/<str:pk>', accept_request, name = "accept_request"),
    path('reject_request/<str:pk>', reject_request, name = "reject_request"),
    path('delete_request/<str:pk>', delete_request, name = "delete_request"),

    path('my-diary', my_diary, name = "my_diary"),
    path('create_entry', create_entry, name = "create_entry"),
    path('reload_entries/<str:kind>', reload_entries, name = "reload_entries"),
    path('delete_entries/<str:pk>', delete_entries, name = "delete_entries"),
    path('filter_entries', filter_entries, name = "filter_entries"),

    path('leaderboards', leaderboards_view, name = "leaderboards"),
    path('register_wkly_game', register_wkly_game, name = "register_wkly_game"),
    path('reload_leaderboards/<str:board>', reload_leaderboards, name = "reload_leaderboards"),

#   sk - group_id
    path('groups', groups, name = "groups"),
    path('group-<str:sk>', group_details, name = "group_details"),
    path('load_more_chats/<str:sk>/<int:page_num>', load_more_chats, name = "load_more_chats"),
    path('mute_user/<int:pk>', mute_user, name = "mute_user"),

    path('group_join-<str:sk>', group_join, name = "group_join"),
    path('group_join_url', group_join_url, name = "group_join_url"),
    path('group_create', group_create, name = "group_create"),
    path('place_admin-<str:sk>', place_admin, name = "place_admin"),
    path('group_edit-<str:sk>', group_edit, name = "group_edit"),
    path('leave-group-<str:sk>', leave_group, name = "leave_group"),
    path('delete-group', delete_group, name = "delete_group"),
    path('remove_from_group/<str:user_id>/<str:sk>', remove_from_group, name = "remove_from_group"),
    path('send_chat-<str:sk>', send_chat, name = "send_chat"),
    path('delete_chat/<str:sk>/<int:msg_id>', delete_chat, name = "delete_chat"),

    path('send_duel_request', send_duel_request, name = "send_duel_request"),
    path('accept_duel', accept_duel, name = "accept_duel"),
    path('reject_duel', reject_duel, name = "reject_duel"),

    path('preview', preview_slip, name = 'preview'),
    path('make-preview-changes', make_preview_changes, name = 'make_preview_changes'),

    path('support', support, name = "support"),
    path('terms', terms, name = "terms"),
    path('privacy-policy', privacy_policy, name = "privacy_policy"),

    path('custom_logout', custom_logout, name = "custom_logout"),
    path('htmx_messages', htmx_messages, name = "htmx_messages"),
]