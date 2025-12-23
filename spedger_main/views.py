from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from render_block import render_block_to_string


# Create your views here.
def home(request):
    xy = ''
    if request.user.is_authenticated:
        xy = 'bread'
    else:
        return redirect('account_login')
    return render(request, 'base.html', {'con': xy})


def signup(request):
    return 