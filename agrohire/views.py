from django.shortcuts import render
from equipment.models import Equipment, EquipmentType
from users.models import User


def home(request):
    """Home page view"""
    context = {
        'equipment_count': Equipment.objects.filter(is_active=True).count(),
        'equipment_types_count': EquipmentType.objects.count(),
        'users_count': User.objects.count(),
    }
    return render(request, 'home.html', context)


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')
