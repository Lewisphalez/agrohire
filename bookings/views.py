from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden
from equipment.models import Equipment
from .models import Booking
from notifications.utils import create_in_app_notification


@login_required
def booking_list(request):
    items = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'bookings/list.html', {'items': items})


@login_required
def booking_create(request):
    equipment_id = request.GET.get('equipment')
    equipment = get_object_or_404(Equipment, pk=equipment_id) if equipment_id else None

    if request.method == 'POST':
        equipment_id = request.POST.get('equipment_id')
        equipment = get_object_or_404(Equipment, pk=equipment_id)
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        duration_hours = request.POST.get('duration_hours')

        booking = Booking(
            user=request.user,
            equipment=equipment,
            start_date=start_date,
            end_date=end_date,
            duration_hours=duration_hours or 8,
            total_amount=equipment.daily_rate,
        )
        if not booking.check_availability():
            messages.error(request, 'Selected time conflicts with another booking.')
        else:
            booking.save()
            # notify owner
            owner = equipment.owner
            create_in_app_notification(
                recipient=owner,
                subject='New booking request',
                body=f"{request.user.get_full_name() or request.user.username} requested {equipment.name} from {start_date} to {end_date}."
            )
            messages.success(request, 'Booking created! The owner has been notified.')
            return redirect('bookings:list')

    return render(request, 'bookings/create.html', {'equipment': equipment})


@login_required
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if booking.status not in ['pending', 'confirmed']:
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('bookings:list')
    booking.cancel('Cancelled by user')
    # notify owner
    create_in_app_notification(
        recipient=booking.equipment.owner,
        subject='Booking cancelled',
        body=f"Booking {booking.booking_number} for {booking.equipment.name} was cancelled by {request.user.get_full_name() or request.user.username}."
    )
    messages.info(request, 'Booking cancelled.')
    return redirect('bookings:list')


@login_required
def owner_bookings(request):
    # show bookings for equipment owned by current owner
    if not getattr(request.user, 'is_equipment_owner', False):
        return HttpResponseForbidden('Only equipment owners.')
    items = Booking.objects.filter(equipment__owner=request.user).order_by('-created_at')
    return render(request, 'bookings/owner_list.html', {'items': items})


@login_required
def booking_confirm(request, pk):
    if not getattr(request.user, 'is_equipment_owner', False):
        return HttpResponseForbidden('Only equipment owners can confirm bookings.')
    booking = get_object_or_404(Booking, pk=pk, equipment__owner=request.user)
    booking.approve(request.user)
    create_in_app_notification(
        recipient=booking.user,
        subject='Booking confirmed',
        body=f"Your booking {booking.booking_number} for {booking.equipment.name} has been confirmed."
    )
    messages.success(request, 'Booking confirmed.')
    return redirect('bookings:owner_list')


@login_required
def booking_reject(request, pk):
    if not getattr(request.user, 'is_equipment_owner', False):
        return HttpResponseForbidden('Only equipment owners can reject bookings.')
    booking = get_object_or_404(Booking, pk=pk, equipment__owner=request.user)
    booking.reject('Rejected by owner')
    create_in_app_notification(
        recipient=booking.user,
        subject='Booking rejected',
        body=f"Your booking {booking.booking_number} for {booking.equipment.name} was rejected by the owner."
    )
    messages.info(request, 'Booking rejected.')
    return redirect('bookings:owner_list')
