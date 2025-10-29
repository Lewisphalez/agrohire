from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Equipment
from .forms import EquipmentForm


def equipment_list(request):
    query = request.GET.get('q', '')
    items = Equipment.objects.filter(is_active=True)
    if query:
        items = items.filter(name__icontains=query)
    return render(request, 'equipment/list.html', {'items': items, 'query': query})


def equipment_detail(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    return render(request, 'equipment/detail.html', {'item': item})


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


