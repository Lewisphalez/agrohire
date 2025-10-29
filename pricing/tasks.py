from celery import shared_task
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from .models import PricingRule, SeasonalPricing, DemandPricing, PricingHistory
from equipment.models import Equipment
from bookings.models import Booking


@shared_task
def update_dynamic_pricing():
    """
    Update dynamic pricing based on demand and seasonal factors
    """
    try:
        today = timezone.now().date()
        
        # Get all active equipment
        equipment_list = Equipment.objects.filter(is_active=True)
        
        for equipment in equipment_list:
            # Calculate demand-based pricing
            demand_multiplier = calculate_demand_multiplier(equipment, today)
            
            # Calculate seasonal pricing
            seasonal_multiplier = calculate_seasonal_multiplier(equipment, today)
            
            # Apply pricing rules
            rule_multiplier = apply_pricing_rules(equipment, today)
            
            # Calculate final multiplier (combine all factors)
            final_multiplier = demand_multiplier * seasonal_multiplier * rule_multiplier
            
            # Update pricing history
            update_pricing_history(equipment, final_multiplier, today)
        
        return f"Updated pricing for {equipment_list.count()} equipment items"
        
    except Exception as e:
        return f"Error updating dynamic pricing: {str(e)}"


@shared_task
def calculate_equipment_pricing(equipment_id, date=None):
    """
    Calculate pricing for a specific equipment on a specific date
    """
    try:
        equipment = Equipment.objects.get(id=equipment_id)
        if not date:
            date = timezone.now().date()
        
        # Calculate all pricing factors
        demand_multiplier = calculate_demand_multiplier(equipment, date)
        seasonal_multiplier = calculate_seasonal_multiplier(equipment, date)
        rule_multiplier = apply_pricing_rules(equipment, date)
        
        final_multiplier = demand_multiplier * seasonal_multiplier * rule_multiplier
        
        # Calculate adjusted rates
        adjusted_hourly_rate = equipment.hourly_rate * final_multiplier
        adjusted_daily_rate = equipment.daily_rate * final_multiplier
        
        return {
            'equipment_id': equipment_id,
            'date': date,
            'demand_multiplier': demand_multiplier,
            'seasonal_multiplier': seasonal_multiplier,
            'rule_multiplier': rule_multiplier,
            'final_multiplier': final_multiplier,
            'adjusted_hourly_rate': adjusted_hourly_rate,
            'adjusted_daily_rate': adjusted_daily_rate
        }
        
    except Equipment.DoesNotExist:
        return f"Equipment with id {equipment_id} not found"
    except Exception as e:
        return f"Error calculating pricing: {str(e)}"


@shared_task
def apply_seasonal_pricing():
    """
    Apply seasonal pricing adjustments
    """
    try:
        today = timezone.now().date()
        seasonal_pricing_list = SeasonalPricing.objects.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )
        
        updated_count = 0
        for seasonal_pricing in seasonal_pricing_list:
            equipment_list = Equipment.objects.filter(
                equipment_type=seasonal_pricing.equipment_type,
                is_active=True
            )
            
            for equipment in equipment_list:
                # Update pricing history
                update_pricing_history(
                    equipment, 
                    seasonal_pricing.daily_multiplier, 
                    today,
                    'seasonal'
                )
                updated_count += 1
        
        return f"Applied seasonal pricing to {updated_count} equipment items"
        
    except Exception as e:
        return f"Error applying seasonal pricing: {str(e)}"


@shared_task
def update_demand_pricing():
    """
    Update pricing based on current demand levels
    """
    try:
        today = timezone.now().date()
        demand_pricing_list = DemandPricing.objects.filter(is_active=True)
        
        updated_count = 0
        for demand_pricing in demand_pricing_list:
            demand_level = demand_pricing.calculate_demand_level(today)
            multiplier = demand_pricing.get_multiplier(demand_level)
            
            equipment_list = Equipment.objects.filter(
                equipment_type=demand_pricing.equipment_type,
                is_active=True
            )
            
            for equipment in equipment_list:
                update_pricing_history(
                    equipment, 
                    multiplier, 
                    today,
                    'demand'
                )
                updated_count += 1
        
        return f"Updated demand pricing for {updated_count} equipment items"
        
    except Exception as e:
        return f"Error updating demand pricing: {str(e)}"


def calculate_demand_multiplier(equipment, date):
    """
    Calculate demand-based pricing multiplier
    """
    try:
        # Look back 7 days for demand calculation
        start_date = date - timedelta(days=7)
        
        # Count bookings for this equipment type
        booking_count = Booking.objects.filter(
            equipment__equipment_type=equipment.equipment_type,
            start_date__gte=start_date,
            start_date__lte=date,
            status__in=['confirmed', 'in_progress']
        ).count()
        
        # Get demand pricing rules
        demand_pricing = DemandPricing.objects.filter(
            equipment_type=equipment.equipment_type,
            is_active=True
        ).first()
        
        if demand_pricing:
            if booking_count <= demand_pricing.low_demand_threshold:
                return demand_pricing.low_demand_multiplier
            elif booking_count >= demand_pricing.high_demand_threshold:
                return demand_pricing.high_demand_multiplier
            else:
                return demand_pricing.normal_demand_multiplier
        
        return 1.0  # Default multiplier
        
    except Exception as e:
        print(f"Error calculating demand multiplier: {e}")
        return 1.0


def calculate_seasonal_multiplier(equipment, date):
    """
    Calculate seasonal pricing multiplier
    """
    try:
        seasonal_pricing = SeasonalPricing.objects.filter(
            equipment_type=equipment.equipment_type,
            is_active=True,
            start_date__lte=date,
            end_date__gte=date
        ).first()
        
        if seasonal_pricing:
            return seasonal_pricing.daily_multiplier
        
        return 1.0  # Default multiplier
        
    except Exception as e:
        print(f"Error calculating seasonal multiplier: {e}")
        return 1.0


def apply_pricing_rules(equipment, date):
    """
    Apply custom pricing rules
    """
    try:
        # Get applicable pricing rules
        applicable_rules = PricingRule.objects.filter(
            Q(equipment=equipment) | Q(equipment_type=equipment.equipment_type),
            is_active=True
        ).order_by('-priority')
        
        if applicable_rules.exists():
            # Use the highest priority rule
            rule = applicable_rules.first()
            
            # Check if rule is applicable for the date
            if rule.is_applicable(equipment, date):
                return rule.daily_multiplier
        
        return 1.0  # Default multiplier
        
    except Exception as e:
        print(f"Error applying pricing rules: {e}")
        return 1.0


def update_pricing_history(equipment, multiplier, date, pricing_type='dynamic'):
    """
    Update pricing history for tracking
    """
    try:
        # Calculate adjusted rates
        adjusted_daily_rate = equipment.daily_rate * multiplier
        
        # Create or update pricing history
        pricing_history, created = PricingHistory.objects.get_or_create(
            equipment=equipment,
            effective_date=date,
            defaults={
                'base_rate': equipment.daily_rate,
                'adjusted_rate': adjusted_daily_rate,
                'multiplier': multiplier,
                'rate_type': 'daily',
                'demand_level': 'normal'  # This could be calculated based on demand
            }
        )
        
        if not created:
            # Update existing record
            pricing_history.adjusted_rate = adjusted_daily_rate
            pricing_history.multiplier = multiplier
            pricing_history.save()
        
        return True
        
    except Exception as e:
        print(f"Error updating pricing history: {e}")
        return False


@shared_task
def cleanup_old_pricing_history():
    """
    Clean up old pricing history records
    """
    try:
        # Keep pricing history for the last 90 days
        cutoff_date = timezone.now().date() - timedelta(days=90)
        
        deleted_count = PricingHistory.objects.filter(
            effective_date__lt=cutoff_date
        ).delete()[0]
        
        return f"Deleted {deleted_count} old pricing history records"
        
    except Exception as e:
        return f"Error cleaning up pricing history: {str(e)}"


@shared_task
def generate_pricing_report():
    """
    Generate pricing analysis report
    """
    try:
        today = timezone.now().date()
        
        # Get pricing statistics
        total_equipment = Equipment.objects.filter(is_active=True).count()
        
        # Equipment with dynamic pricing
        equipment_with_dynamic_pricing = Equipment.objects.filter(
            is_active=True,
            pricing_rules__is_active=True
        ).distinct().count()
        
        # Average pricing multiplier
        recent_pricing = PricingHistory.objects.filter(
            effective_date=today
        )
        
        if recent_pricing.exists():
            avg_multiplier = recent_pricing.aggregate(
                avg_multiplier=models.Avg('multiplier')
            )['avg_multiplier']
        else:
            avg_multiplier = 1.0
        
        report = {
            'date': today,
            'total_equipment': total_equipment,
            'equipment_with_dynamic_pricing': equipment_with_dynamic_pricing,
            'average_multiplier': avg_multiplier,
            'generated_at': timezone.now()
        }
        
        return report
        
    except Exception as e:
        return f"Error generating pricing report: {str(e)}"
