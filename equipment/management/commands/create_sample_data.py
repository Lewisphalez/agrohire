from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from equipment.models import EquipmentType, Equipment
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample equipment data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample equipment data...')
        
        # Create equipment types
        equipment_types = [
            {
                'name': 'Tractor',
                'category': 'tractor',
                'description': 'Agricultural tractor for farming operations',
                'base_daily_rate': Decimal('5000.00'),
                'base_hourly_rate': Decimal('500.00'),
            },
            {
                'name': 'Harvester',
                'category': 'harvester',
                'description': 'Grain harvester for crop harvesting',
                'base_daily_rate': Decimal('8000.00'),
                'base_hourly_rate': Decimal('800.00'),
            },
            {
                'name': 'Planter',
                'category': 'planter',
                'description': 'Seed planter for crop planting',
                'base_daily_rate': Decimal('3000.00'),
                'base_hourly_rate': Decimal('300.00'),
            },
            {
                'name': 'Irrigation System',
                'category': 'irrigation',
                'description': 'Irrigation system for crop watering',
                'base_daily_rate': Decimal('2000.00'),
                'base_hourly_rate': Decimal('200.00'),
            },
            {
                'name': 'Sprayer',
                'category': 'sprayer',
                'description': 'Crop sprayer for pesticides and fertilizers',
                'base_daily_rate': Decimal('1500.00'),
                'base_hourly_rate': Decimal('150.00'),
            },
            {
                'name': 'Tillage Equipment',
                'category': 'tillage',
                'description': 'Tillage implements like ploughs and harrows',
                'base_daily_rate': Decimal('1800.00'),
                'base_hourly_rate': Decimal('180.00'),
            },
            {
                'name': 'Transport Trailer',
                'category': 'transport',
                'description': 'Trailers and transport vehicles for farm produce',
                'base_daily_rate': Decimal('2500.00'),
                'base_hourly_rate': Decimal('250.00'),
            },
        ]
        
        created_types = {}
        for type_data in equipment_types:
            equipment_type, created = EquipmentType.objects.get_or_create(
                name=type_data['name'],
                defaults=type_data
            )
            created_types[type_data['category']] = equipment_type
            if created:
                self.stdout.write(f'Created equipment type: {equipment_type.name}')
            else:
                self.stdout.write(f'Equipment type already exists: {equipment_type.name}')
        
        # Create sample users if they don't exist
        equipment_owner, created = User.objects.get_or_create(
            username='equipment_owner',
            defaults={
                'email': 'owner@agrohire.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'equipment_owner',
                'phone_number': '+254700000000',
                'business_name': 'Doe Farm Equipment',
                'is_verified': True,
            }
        )
        if created:
            equipment_owner.set_password('password123')
            equipment_owner.save()
            self.stdout.write('Created equipment owner user')
        
        second_owner, created = User.objects.get_or_create(
            username='owner_kamau',
            defaults={
                'email': 'kamau@agrohire.com',
                'first_name': 'Kamau',
                'last_name': 'Mwangi',
                'role': 'equipment_owner',
                'phone_number': '+254711111111',
                'business_name': 'Kamau Agro Services',
                'is_verified': True,
            }
        )
        if created:
            second_owner.set_password('password123')
            second_owner.save()
            self.stdout.write('Created second equipment owner user')
        
        owners = [equipment_owner, second_owner]
        
        # Create sample equipment (significantly expanded)
        sample_equipment = [
            {
                'name': 'Kubota Tractor L3901',
                'equipment_type': created_types['tractor'],
                'description': 'Reliable 39HP tractor perfect for small to medium farms',
                'model': 'L3901',
                'year_manufactured': 2020,
                'condition': 'excellent',
                'daily_rate': Decimal('5500.00'),
                'hourly_rate': Decimal('550.00'),
                'latitude': Decimal('-1.2921'),
                'longitude': Decimal('36.8219'),
                'address': 'Nairobi, Kenya',
                'city': 'Nairobi',
                'state': 'Nairobi',
                'fuel_type': 'diesel',
                'capacity': '39 HP',
            },
            {
                'name': 'John Deere Harvester 9870',
                'equipment_type': created_types['harvester'],
                'description': 'High-capacity grain harvester for large farms',
                'model': '9870',
                'year_manufactured': 2019,
                'condition': 'good',
                'daily_rate': Decimal('8500.00'),
                'hourly_rate': Decimal('850.00'),
                'latitude': Decimal('-0.0917'),
                'longitude': Decimal('34.7680'),
                'address': 'Kisumu, Kenya',
                'city': 'Kisumu',
                'state': 'Kisumu',
                'fuel_type': 'diesel',
                'capacity': '450 HP',
            },
            {
                'name': 'New Holland TT75 Tractor',
                'equipment_type': created_types['tractor'],
                'description': 'Durable 75HP tractor for tough field work',
                'model': 'TT75',
                'year_manufactured': 2018,
                'condition': 'good',
                'daily_rate': Decimal('5200.00'),
                'hourly_rate': Decimal('520.00'),
                'latitude': Decimal('-0.4167'),
                'longitude': Decimal('36.9510'),
                'address': 'Nyeri, Kenya',
                'city': 'Nyeri',
                'state': 'Nyeri',
                'fuel_type': 'diesel',
                'capacity': '75 HP',
            },
            {
                'name': 'Massey Ferguson 290 Tractor',
                'equipment_type': created_types['tractor'],
                'description': 'Popular MF 290, reliable and efficient',
                'model': 'MF 290',
                'year_manufactured': 2017,
                'condition': 'fair',
                'daily_rate': Decimal('4800.00'),
                'hourly_rate': Decimal('480.00'),
                'latitude': Decimal('-0.1022'),
                'longitude': Decimal('34.7617'),
                'address': 'Kisumu, Kenya',
                'city': 'Kisumu',
                'state': 'Kisumu',
                'fuel_type': 'diesel',
                'capacity': '80 HP',
            },
            {
                'name': 'Precision Planter 12-Row',
                'equipment_type': created_types['planter'],
                'description': 'Precision seed planter for optimal crop spacing',
                'model': '12-Row',
                'year_manufactured': 2021,
                'condition': 'excellent',
                'daily_rate': Decimal('3200.00'),
                'hourly_rate': Decimal('320.00'),
                'latitude': Decimal('0.5143'),
                'longitude': Decimal('35.2698'),
                'address': 'Eldoret, Kenya',
                'city': 'Eldoret',
                'state': 'Uasin Gishu',
                'fuel_type': 'diesel',
                'capacity': '12 rows',
            },
            {
                'name': 'Seed Drill 24-Run',
                'equipment_type': created_types['planter'],
                'description': '24-run seed drill for cereals',
                'model': 'SD-24',
                'year_manufactured': 2019,
                'condition': 'good',
                'daily_rate': Decimal('2700.00'),
                'hourly_rate': Decimal('270.00'),
                'latitude': Decimal('-0.0917'),
                'longitude': Decimal('34.7680'),
                'address': 'Kisumu, Kenya',
                'city': 'Kisumu',
                'state': 'Kisumu',
                'fuel_type': 'other',
                'capacity': '24 rows',
            },
            {
                'name': 'Boom Sprayer 600L',
                'equipment_type': created_types['sprayer'],
                'description': 'Tractor-mounted boom sprayer 600 liters',
                'model': 'BS-600',
                'year_manufactured': 2022,
                'condition': 'excellent',
                'daily_rate': Decimal('1600.00'),
                'hourly_rate': Decimal('160.00'),
                'latitude': Decimal('-1.2864'),
                'longitude': Decimal('36.8172'),
                'address': 'Nairobi, Kenya',
                'city': 'Nairobi',
                'state': 'Nairobi',
                'fuel_type': 'other',
                'capacity': '600 L',
            },
            {
                'name': 'Knapsack Sprayer 20L',
                'equipment_type': created_types['sprayer'],
                'description': 'Manual knapsack sprayer for small plots',
                'model': 'KS-20',
                'year_manufactured': 2022,
                'condition': 'excellent',
                'daily_rate': Decimal('800.00'),
                'hourly_rate': Decimal('80.00'),
                'latitude': Decimal('-3.3753'),
                'longitude': Decimal('36.8356'),
                'address': 'Arusha, Tanzania',
                'city': 'Arusha',
                'state': 'Arusha',
                'fuel_type': 'other',
                'capacity': '20 L',
            },
            {
                'name': 'Center Pivot Segment',
                'equipment_type': created_types['irrigation'],
                'description': 'Center pivot irrigation segment rental',
                'model': 'CP-SEG',
                'year_manufactured': 2020,
                'condition': 'good',
                'daily_rate': Decimal('4500.00'),
                'hourly_rate': Decimal('450.00'),
                'latitude': Decimal('0.0463'),
                'longitude': Decimal('37.6559'),
                'address': 'Meru, Kenya',
                'city': 'Meru',
                'state': 'Meru',
                'fuel_type': 'other',
                'capacity': 'Segment',
            },
            {
                'name': 'Irrigation Pump 3"',
                'equipment_type': created_types['irrigation'],
                'description': 'Portable irrigation water pump 3-inch',
                'model': 'PMP-3',
                'year_manufactured': 2023,
                'condition': 'excellent',
                'daily_rate': Decimal('1200.00'),
                'hourly_rate': Decimal('120.00'),
                'latitude': Decimal('0.0463'),
                'longitude': Decimal('37.6559'),
                'address': 'Meru, Kenya',
                'city': 'Meru',
                'state': 'Meru',
                'fuel_type': 'petrol',
                'capacity': '3 inch',
            },
            {
                'name': 'Disc Harrow 16-Disc',
                'equipment_type': created_types['tillage'],
                'description': 'Heavy-duty disc harrow for soil preparation',
                'model': 'DH-16',
                'year_manufactured': 2018,
                'condition': 'good',
                'daily_rate': Decimal('2000.00'),
                'hourly_rate': Decimal('200.00'),
                'latitude': Decimal('-1.2921'),
                'longitude': Decimal('36.8219'),
                'address': 'Nairobi, Kenya',
                'city': 'Nairobi',
                'state': 'Nairobi',
                'fuel_type': 'other',
                'capacity': '16 discs',
            },
            {
                'name': 'Subsoiler 3-Shank',
                'equipment_type': created_types['tillage'],
                'description': '3-shank subsoiler for deep tillage',
                'model': 'SS-3',
                'year_manufactured': 2019,
                'condition': 'good',
                'daily_rate': Decimal('2100.00'),
                'hourly_rate': Decimal('210.00'),
                'latitude': Decimal('-0.3031'),
                'longitude': Decimal('36.0800'),
                'address': 'Nakuru, Kenya',
                'city': 'Nakuru',
                'state': 'Nakuru',
                'fuel_type': 'other',
                'capacity': '3 shank',
            },
            {
                'name': 'Transport Trailer 5T',
                'equipment_type': created_types['transport'],
                'description': '5-ton farm trailer for transport',
                'model': 'TR-5T',
                'year_manufactured': 2020,
                'condition': 'excellent',
                'daily_rate': Decimal('2600.00'),
                'hourly_rate': Decimal('260.00'),
                'latitude': Decimal('-0.1022'),
                'longitude': Decimal('34.7617'),
                'address': 'Kisumu, Kenya',
                'city': 'Kisumu',
                'state': 'Kisumu',
                'fuel_type': 'other',
                'capacity': '5 tons',
            },
            {
                'name': 'Flatbed Trailer 10T',
                'equipment_type': created_types['transport'],
                'description': '10-ton flatbed trailer for produce transport',
                'model': 'FB-10',
                'year_manufactured': 2021,
                'condition': 'excellent',
                'daily_rate': Decimal('3400.00'),
                'hourly_rate': Decimal('340.00'),
                'latitude': Decimal('-1.2864'),
                'longitude': Decimal('36.8172'),
                'address': 'Nairobi, Kenya',
                'city': 'Nairobi',
                'state': 'Nairobi',
                'fuel_type': 'other',
                'capacity': '10 tons',
            },
            {
                'name': 'Round Baler RB560',
                'equipment_type': created_types['tractor'],
                'description': 'Round baler attachment for hay baling',
                'model': 'RB560',
                'year_manufactured': 2017,
                'condition': 'good',
                'daily_rate': Decimal('4500.00'),
                'hourly_rate': Decimal('450.00'),
                'latitude': Decimal('-0.0917'),
                'longitude': Decimal('34.7680'),
                'address': 'Kisumu, Kenya',
                'city': 'Kisumu',
                'state': 'Kisumu',
                'fuel_type': 'other',
                'capacity': 'Round bales',
            },
            {
                'name': 'Maize Sheller Mobile',
                'equipment_type': created_types['harvester'],
                'description': 'Mobile maize sheller service',
                'model': 'MS-900',
                'year_manufactured': 2020,
                'condition': 'excellent',
                'daily_rate': Decimal('3000.00'),
                'hourly_rate': Decimal('300.00'),
                'latitude': Decimal('-0.0236'),
                'longitude': Decimal('37.9062'),
                'address': 'Kenya',
                'city': 'Thika',
                'state': 'Kiambu',
                'fuel_type': 'diesel',
                'capacity': 'High throughput',
            },
            {
                'name': 'Potato Planter 2-Row',
                'equipment_type': created_types['planter'],
                'description': 'Two-row potato planter for seed tubers',
                'model': 'PP-2',
                'year_manufactured': 2018,
                'condition': 'good',
                'daily_rate': Decimal('2900.00'),
                'hourly_rate': Decimal('290.00'),
                'latitude': Decimal('0.5167'),
                'longitude': Decimal('35.2833'),
                'address': 'Eldoret, Kenya',
                'city': 'Eldoret',
                'state': 'Uasin Gishu',
                'fuel_type': 'other',
                'capacity': '2 rows',
            },
            {
                'name': 'Forage Harvester Pull-Type',
                'equipment_type': created_types['harvester'],
                'description': 'Pull-type forage harvester for silage',
                'model': 'FH-PT',
                'year_manufactured': 2016,
                'condition': 'fair',
                'daily_rate': Decimal('4200.00'),
                'hourly_rate': Decimal('420.00'),
                'latitude': Decimal('-1.2921'),
                'longitude': Decimal('36.8219'),
                'address': 'Nairobi, Kenya',
                'city': 'Nairobi',
                'state': 'Nairobi',
                'fuel_type': 'diesel',
                'capacity': 'Silage',
            },
            {
                'name': 'Water Bowser 5000L',
                'equipment_type': created_types['transport'],
                'description': '5000L water bowser for irrigation support',
                'model': 'WB-5K',
                'year_manufactured': 2021,
                'condition': 'excellent',
                'daily_rate': Decimal('3500.00'),
                'hourly_rate': Decimal('350.00'),
                'latitude': Decimal('-0.3031'),
                'longitude': Decimal('36.0800'),
                'address': 'Nakuru, Kenya',
                'city': 'Nakuru',
                'state': 'Nakuru',
                'fuel_type': 'diesel',
                'capacity': '5000 L',
            },
        ]
        
        for idx, equipment_data in enumerate(sample_equipment):
            owner = owners[idx % len(owners)]
            equipment, created = Equipment.objects.get_or_create(
                name=equipment_data['name'],
                defaults={
                    **equipment_data,
                    'owner': owner,
                }
            )
            if created:
                self.stdout.write(f'Created equipment: {equipment.name}')
            else:
                self.stdout.write(f'Equipment already exists: {equipment.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample equipment data!')
        )
        self.stdout.write('Admin: /admin/ (admin / admin123)')
        self.stdout.write('Owners: equipment_owner / password123, owner_kamau / password123')
