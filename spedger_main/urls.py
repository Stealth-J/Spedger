from django.urls import path
from .views import *

urlpatterns = [
    path('home', home, name = "home"),
    path('signup', signup, name = "signup"),
    path('profile/<str:sk>', profile, name = "profile"),
    path('delete_acct/<str:sk>', delete_acct, name = "delete_acct"),
    path('settings', account_settings, name = "settings"),
    path('users', users, name = "users"),
    path('search_users', search_users, name = "search_users"),

    path('send_friend_request/<str:sk>', send_friend_request, name = "send_friend_request"),
    path('accept_request/<str:pk>', accept_request, name = "accept_request"),
    path('reject_request/<str:pk>', reject_request, name = "reject_request"),
    path('delete_request/<str:pk>', delete_request, name = "delete_request"),

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