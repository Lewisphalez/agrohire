from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, Count, Q

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
    user = request.user
    if user.is_staff or user.is_superuser:
        return redirect('users:admin_dashboard')

    now = timezone.now()
    my_bookings = Booking.objects.filter(user=user).order_by('-created_at')[:5]
    upcoming = Booking.objects.filter(user=user, start_date__gte=now).order_by('start_date')[:3]
    stats = {
        'total_bookings': Booking.objects.filter(user=user).count(),
        'active_bookings': Booking.objects.filter(user=user, status__in=['confirmed', 'in_progress']).count(),
        'completed_bookings': Booking.objects.filter(user=user, status='completed').count(),
    }

    context = {
        'stats': stats,
        'upcoming': upcoming,
        'my_bookings': my_bookings,
    }

    if getattr(user, 'is_equipment_owner', False):
        owned_equipment = Equipment.objects.filter(owner=user)
        owner_stats = {
            'owned_count': owned_equipment.count(),
            'total_earnings': Payment.objects.filter(booking__equipment__in=owned_equipment, status='completed').aggregate(total=Sum('amount'))['total'] or 0,
            'booking_requests': Booking.objects.filter(equipment__in=owned_equipment, status__in=['pending', 'confirmed']).count(),
        }
        context['owner_stats'] = owner_stats
        context['owned_equipment'] = owned_equipment.order_by('-created_at')[:5]

    return render(request, 'users/dashboard.html', context)


@login_required
def admin_dashboard_view(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    stats = {
        'total_users': User.objects.count(),
        'total_equipment': Equipment.objects.count(),
        'total_bookings': Booking.objects.count(),
        'total_revenue': Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0,
    }

    context = {
        'stats': stats,
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'recent_bookings': Booking.objects.order_by('-created_at')[:5],
    }
    return render(request, 'users/admin_dashboard.html', context)


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
