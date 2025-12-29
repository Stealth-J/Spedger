from django.urls import path
from .views import *

urlpatterns = [
    path('home', home, name = "home"),
    path('signup', signup, name = "signup"),
    path('profile/<str:sk>', profile, name = "profile"),
    path('delete_acct/<str:sk>', delete_acct, name = "delete_acct"),
    path('settings', settings, name = "settings"),
    path('support', support, name = "support"),
    path('terms', terms, name = "terms"),
    path('privacy-policy', privacy_policy, name = "privacy_policy"),
    path('custom_logout', custom_logout, name = "custom_logout"),

    path('htmx_messages', htmx_messages, name = "htmx_messages"),
]