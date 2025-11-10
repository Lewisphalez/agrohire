from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Equipment, EquipmentType
from .forms import EquipmentForm
from pricing.models import SeasonalPricing
from django.utils import timezone

def equipment_list(request):
    items = Equipment.objects.filter(is_active=True)
    
    # Get filter parameters from request
    type_filter = request.GET.get('type')
    city_filter = request.GET.get('city')
    query = request.GET.get('q', '')

    if query:
        items = items.filter(name__icontains=query)
    if type_filter:
        items = items.filter(equipment_type__id=type_filter)
    if city_filter:
        items = items.filter(city__iexact=city_filter)

    # Get choices for filters
    equipment_types = EquipmentType.objects.all()
    cities = Equipment.objects.values_list('city', flat=True).distinct()

    context = {
        'items': items,
        'equipment_types': equipment_types,
        'cities': cities,
        'query': query,
        'type_filter': type_filter,
        'city_filter': city_filter,
    }
    return render(request, 'equipment/list.html', context)

def equipment_detail(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    
    # Dynamic Pricing Logic
    original_price = item.daily_rate
    new_price = original_price
    price_has_changed = False
    
    today = timezone.now().date()
    seasonal_rule = SeasonalPricing.objects.filter(
        equipment_type=item.equipment_type,
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).first()
    
    if seasonal_rule:
        multiplier = seasonal_rule.daily_multiplier
        new_price = original_price * multiplier
        price_has_changed = True
        
    context = {
        'item': item,
        'original_price': original_price,
        'new_price': new_price,
        'price_has_changed': price_has_changed,
    }
    
    return render(request, 'equipment/detail.html', context)


@login_required
def my_equipment_list(request):
    if not getattr(request.user, 'is_equipment_owner', False):
        return HttpResponseForbidden('Only equipment owners can access this page.')
    items = Equipment.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'equipment/my_list.html', {'items': items})


@login_required
def equipment_create(request):
    if not getattr(request.user, 'is_equipment_owner', False):
        return HttpResponseForbidden('Only equipment owners can add equipment.')
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.owner = request.user
            equipment.save()
            messages.success(request, 'Equipment created successfully!')
            return redirect('equipment:my_list')
    else:
        form = EquipmentForm()
    return render(request, 'equipment/form.html', {'form': form, 'title': 'Add Equipment'})


@login_required
def equipment_edit(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Equipment updated successfully!')
            return redirect('equipment:my_list')
    else:
        form = EquipmentForm(instance=equipment)
    return render(request, 'equipment/form.html', {'form': form, 'title': 'Edit Equipment'})


@login_required
def equipment_delete(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk, owner=request.user)
    if request.method == 'POST':
        equipment.delete()
        messages.info(request, 'Equipment deleted.')
        return redirect('equipment:my_list')
    return render(request, 'equipment/confirm_delete.html', {'item': equipment})


