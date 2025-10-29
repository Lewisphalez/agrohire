from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import random
from equipment.models import Equipment, EquipmentType
from bookings.models import Booking
from users.models import User
from maintenance.models import (
    EquipmentUsageLog, 
    MaintenanceRecord
)


class Command(BaseCommand):
    help = 'Generate historical equipment usage and maintenance data for ML training'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=12,
            help='Number of months of historical data to generate (default: 12)'
        )
        parser.add_argument(
            '--bookings-per-equipment',
            type=int,
            default=20,
            help='Average number of bookings per equipment (default: 20)'
        )
    
    def handle(self, *args, **options):
        months = options['months']
        bookings_per_equipment = options['bookings_per_equipment']
        
        self.stdout.write(self.style.SUCCESS(
            f'\n🚀 Starting historical data generation...\n'
            f'   Months: {months}\n'
            f'   Bookings per equipment: {bookings_per_equipment}\n'
        ))
        
        # Get all equipment
        equipment_list = list(Equipment.objects.all())
        
        if not equipment_list:
            self.stdout.write(self.style.ERROR(
                '❌ No equipment found! Please add equipment first.'
            ))
            return
        
        # Get a sample user for bookings
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR(
                '❌ No users found! Please create users first.'
            ))
            return
        
        total_bookings_created = 0
        total_usage_logs_created = 0
        total_maintenance_records_created = 0
        
        for equipment in equipment_list:
            self.stdout.write(f'\n📦 Processing: {equipment.name}...')
            
            # Generate bookings and usage logs
            num_bookings = random.randint(
                int(bookings_per_equipment * 0.7), 
                int(bookings_per_equipment * 1.3)
            )
            
            current_date = timezone.now() - timedelta(days=months * 30)
            cumulative_hours = equipment.total_hours or 0
            cumulative_km = equipment.total_kilometers if hasattr(equipment, 'total_kilometers') else 0
            
            for i in range(num_bookings):
                # Random booking duration (1-7 days)
                duration_days = random.randint(1, 7)
                duration_hours = duration_days * random.randint(6, 10)  # Hours per day
                
                # Create booking
                start_date = current_date + timedelta(days=random.randint(1, 15))
                end_date = start_date + timedelta(days=duration_days)
                
                booking = Booking.objects.create(
                    user=random.choice(users),
                    equipment=equipment,
                    start_date=start_date,
                    end_date=end_date,
                    actual_start_date=start_date,
                    actual_end_date=end_date,
                    duration_hours=duration_hours,
                    total_amount=Decimal(duration_hours) * equipment.hourly_rate,
                    status='completed'
                )
                total_bookings_created += 1
                
                # Generate usage log
                hours_used = Decimal(duration_hours) * Decimal(random.uniform(0.8, 1.0))
                km_covered = float(hours_used) * random.uniform(3, 8)  # km per hour
                fuel_consumed = float(hours_used) * float(equipment.fuel_consumption or 5)
                
                # Add some randomness based on equipment type
                terrain_types = ['flat', 'hilly', 'rough', 'mixed']
                terrain_weights = [0.4, 0.3, 0.2, 0.1]
                
                usage_log = EquipmentUsageLog.objects.create(
                    booking=booking,
                    equipment=equipment,
                    hours_used=hours_used,
                    kilometers_covered=Decimal(km_covered),
                    fuel_consumed=Decimal(fuel_consumed),
                    operating_temperature_avg=Decimal(random.uniform(60, 95)),
                    load_factor=Decimal(random.uniform(40, 85)),
                    terrain_type=random.choices(terrain_types, weights=terrain_weights)[0],
                    idle_time_hours=Decimal(random.uniform(0.1, 2.0)),
                    error_count=random.randint(0, 3)
                )
                total_usage_logs_created += 1
                
                # Update cumulative metrics
                cumulative_hours += int(hours_used)
                cumulative_km += int(km_covered)
                
                # Move time forward
                current_date = end_date + timedelta(days=random.randint(1, 7))
                
                # Generate maintenance records based on cumulative hours
                if equipment.equipment_type.category in ['tractor', 'harvester']:
                    maintenance_interval = 250
                else:
                    maintenance_interval = 400
                
                if cumulative_hours % maintenance_interval < duration_hours:
                    # Time for maintenance!
                    maintenance_date = end_date + timedelta(days=random.randint(1, 5))
                    
                    maintenance_types = ['preventive', 'corrective']
                    maintenance_type = random.choice(maintenance_types)
                    
                    # Generate issues based on usage patterns
                    issues = []
                    if usage_log.load_factor > 75:
                        issues.append("High load operation detected")
                    if usage_log.error_count > 1:
                        issues.append(f"{usage_log.error_count} error codes logged")
                    if usage_log.terrain_type == 'rough':
                        issues.append("Rough terrain wear observed")
                    
                    parts_replaced = []
                    parts_cost = Decimal(0)
                    
                    if maintenance_type == 'preventive':
                        parts_replaced = [
                            {'part': 'Engine Oil', 'quantity': 1, 'cost': 2500},
                            {'part': 'Oil Filter', 'quantity': 1, 'cost': 800},
                            {'part': 'Air Filter', 'quantity': 1, 'cost': 1200}
                        ]
                        parts_cost = sum(p['cost'] for p in parts_replaced)
                    else:
                        possible_parts = [
                            {'part': 'Brake Pads', 'quantity': 1, 'cost': 4500},
                            {'part': 'Hydraulic Hose', 'quantity': 2, 'cost': 3000},
                            {'part': 'Belt', 'quantity': 1, 'cost': 2000},
                            {'part': 'Spark Plugs', 'quantity': 4, 'cost': 1600},
                        ]
                        parts_replaced = random.sample(possible_parts, random.randint(1, 3))
                        parts_cost = sum(p['cost'] for p in parts_replaced)
                    
                    labor_cost = Decimal(random.randint(5000, 15000))
                    
                    maintenance_record = MaintenanceRecord.objects.create(
                        equipment=equipment,
                        maintenance_type=maintenance_type,
                        status='completed',
                        scheduled_date=maintenance_date,
                        completed_date=maintenance_date + timedelta(hours=random.randint(2, 8)),
                        description=f"Scheduled {maintenance_type} maintenance at {cumulative_hours} hours",
                        work_performed="Standard service: " + ", ".join(p['part'] for p in parts_replaced),
                        parts_replaced=parts_replaced,
                        equipment_hours_at_maintenance=cumulative_hours,
                        kilometers_at_maintenance=cumulative_km,
                        labor_cost=labor_cost,
                        parts_cost=Decimal(parts_cost),
                        total_cost=labor_cost + Decimal(parts_cost),
                        performed_by=f"Technician {random.randint(1, 5)}",
                        issues_found="; ".join(issues) if issues else "No major issues",
                        severity='low' if not issues else random.choice(['low', 'medium']),
                        next_maintenance_due=(maintenance_date + timedelta(days=90)).date()
                    )
                    total_maintenance_records_created += 1
            
            # Update equipment with final cumulative values
            equipment.total_hours = cumulative_hours
            if hasattr(equipment, 'total_kilometers'):
                equipment.total_kilometers = cumulative_km
            equipment.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'   ✅ Created {num_bookings} bookings for {equipment.name}'
            ))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\n✨ Data generation complete!\n'
            f'   📋 Total Bookings: {total_bookings_created}\n'
            f'   📊 Total Usage Logs: {total_usage_logs_created}\n'
            f'   🔧 Total Maintenance Records: {total_maintenance_records_created}\n'
        ))