"""
Views for accounts app: registration, login, logout, and profile management.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from compiler_lab.models import AnalysisRecord


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to CodeCraft, {user.username}! Your lab account has been created.")
            return redirect('dashboard:index')
        else:
            messages.error(request, "Please correct the registration errors below.")
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('dashboard:index')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })


def logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f"You have been successfully logged out, {username}.")
    return redirect('home')


@login_required
def profile_view(request):
    user_analyses = AnalysisRecord.objects.filter(user=request.user)
    total_count = user_analyses.count()
    success_count = user_analyses.filter(is_success=True).count()
    failed_count = user_analyses.filter(is_success=False).count()

    context = {
        'total_count': total_count,
        'success_count': success_count,
        'failed_count': failed_count,
        'recent_analyses': user_analyses[:5],
    }
    return render(request, 'accounts/profile.html', context)
