from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone

from .forms import SignUpForm, LoginForm, UserProfileForm
from .models import User
from bookings.models import Booking
from equipment.models import Equipment
from payments.models import Payment


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Welcome back!')
            return redirect('dashboard')
    else:
        form = LoginForm(request)
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('users:login')


@login_required
def dashboard_view(request):
    now = timezone.now()
    user = request.user

    # Bookings summary for this user
    my_bookings = Booking.objects.filter(user=user).order_by('-created_at')[:5]
    upcoming = Booking.objects.filter(user=user, start_date__gte=now).order_by('start_date')[:3]
    stats = {
        'total_bookings': Booking.objects.filter(user=user).count(),
        'active_bookings': Booking.objects.filter(user=user, status__in=['confirmed', 'in_progress']).count(),
        'completed_bookings': Booking.objects.filter(user=user, status='completed').count(),
    }

    # If equipment owner, show owned equipment snapshot
    owned_equipment = []
    owned_count = 0
    if getattr(user, 'is_equipment_owner', False):
        owned_qs = Equipment.objects.filter(owner=user)
        owned_count = owned_qs.count()
        owned_equipment = owned_qs.order_by('-created_at')[:5]

    # Payments snapshot
    recent_payments = Payment.objects.filter(user=user).order_by('-created_at')[:5]
    payments_stats = {
        'total_payments': Payment.objects.filter(user=user).count(),
        'completed_payments': Payment.objects.filter(user=user, status='completed').count(),
        'pending_payments': Payment.objects.filter(user=user, status__in=['pending', 'processing']).count(),
    }

    context = {
        'stats': stats,
        'upcoming': upcoming,
        'my_bookings': my_bookings,
        'owned_equipment': owned_equipment,
        'owned_count': owned_count,
        'recent_payments': recent_payments,
        'payments_stats': payments_stats,
    }
    return render(request, 'users/dashboard.html', context)


@login_required
def profile_view(request):
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            prof = form.save(commit=False)
            prof.user = request.user
            prof.save()
            messages.success(request, 'Profile updated!')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'users/profile.html', {'form': form})
