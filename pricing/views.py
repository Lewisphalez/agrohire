from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from equipment.models import Equipment
from .models import SeasonalPricing

def test_price(request, equipment_id):
    """
    A simple view to test dynamic pricing for a piece of equipment.
    """
    try:
        equipment = Equipment.objects.get(id=equipment_id)
        original_price = equipment.daily_rate
        
        # Find an active seasonal pricing rule for this equipment type
        today = timezone.now().date()
        seasonal_rule = SeasonalPricing.objects.filter(
            equipment_type=equipment.equipment_type,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).first()
        
        if seasonal_rule:
            multiplier = seasonal_rule.daily_multiplier
            new_price = original_price * multiplier
            price_has_changed = True
        else:
            multiplier = 1.0
            new_price = original_price
            price_has_changed = False
            
        return JsonResponse({
            'equipment_name': equipment.name,
            'original_price': original_price,
            'new_price': new_price,
            'multiplier': multiplier,
            'price_has_changed': price_has_changed,
            'rule_applied': seasonal_rule.name if seasonal_rule else None
        })
        
    except Equipment.DoesNotExist:
        return JsonResponse({'error': 'Equipment not found'}, status=404)
