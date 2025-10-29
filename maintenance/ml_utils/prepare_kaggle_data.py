"""
This script downloads and prepares equipment maintenance data from Kaggle.

KAGGLE DATASET RECOMMENDATION:
- "Predictive Maintenance Dataset AI4I 2020" by Stephan Matzka
- Link: https://www.kaggle.com/datasets/stephanmatzka/predictive-maintenance-dataset-ai4i-2020

To use this:
1. Install kaggle: pip install kaggle
2. Set up Kaggle API credentials: https://github.com/Kaggle/kaggle-api
3. Run: python maintenance/ml_utils/prepare_kaggle_data.py
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add Django project to path
project_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_path))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrohire.settings')
import django
django.setup()


class KaggleDataPreparation:
    """Prepare Kaggle maintenance dataset for our model"""
    
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.data_dir = self.base_dir / 'data'
        self.data_dir.mkdir(exist_ok=True)
    
    def download_dataset(self):
        """Download dataset from Kaggle"""
        print("📥 Downloading dataset from Kaggle...")
        
        try:
            import kaggle
            
            # Download predictive maintenance dataset
            kaggle.api.dataset_download_files(
                'stephanmatzka/predictive-maintenance-dataset-ai4i-2020',
                path=self.data_dir,
                unzip=True
            )
            print("✅ Dataset downloaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading: {e}")
            print("\n💡 Alternative: Download manually from:")
            print("   https://www.kaggle.com/datasets/stephanmatzka/predictive-maintenance-dataset-ai4i-2020")
            print(f"   and place in: {self.data_dir}")
            return False
    
    def generate_synthetic_data(self, num_records=5000):
        """Generate synthetic data if Kaggle download fails"""
        print(f"\n🎲 Generating {num_records} synthetic records...")
        
        np.random.seed(42)
        
        # Equipment types with different characteristics
        equipment_types = ['tractor', 'harvester', 'planter', 'other']
        
        data = []
        for i in range(num_records):
            equipment_type = np.random.choice(equipment_types)
            
            # Base values depend on equipment type
            if equipment_type in ['tractor', 'harvester']:
                base_hours = np.random.uniform(100, 2000)
                failure_rate = 0.25
            else:
                base_hours = np.random.uniform(50, 1000)
                failure_rate = 0.15
            
            record = {
                'equipment_type': equipment_type,
                'hours_used': np.random.uniform(5, 50),
                'kilometers_covered': np.random.uniform(20, 400),
                'fuel_consumed': np.random.uniform(10, 150),
                'operating_temperature_avg': np.random.uniform(60, 100),
                'load_factor': np.random.uniform(30, 90),
                'terrain_type': np.random.choice(['flat', 'hilly', 'rough', 'mixed']),
                'idle_time_hours': np.random.uniform(0, 5),
                'error_count': np.random.poisson(1),
                'cumulative_hours': base_hours + np.random.uniform(0, 500),
                'cumulative_km': base_hours * np.random.uniform(3, 8),
                'days_since_last_maintenance': np.random.uniform(1, 180),
                'maintenance_needed': np.random.choice([0, 1], p=[1-failure_rate, failure_rate])
            }
            
            # Add some correlations
            if record['cumulative_hours'] > 1500:
                record['maintenance_needed'] = 1 if np.random.random() < 0.6 else 0
            
            if record['error_count'] > 2:
                record['maintenance_needed'] = 1 if np.random.random() < 0.7 else 0
            
            if record['days_since_last_maintenance'] > 120:
                record['maintenance_needed'] = 1 if np.random.random() < 0.5 else 0
            
            data.append(record)
        
        df = pd.DataFrame(data)
        
        # Save synthetic data
        output_file = self.data_dir / 'synthetic_maintenance_data.csv'
        df.to_csv(output_file, index=False)
        print(f"✅ Synthetic data saved to: {output_file}")
        print(f"   Shape: {df.shape}")
        print(f"\n📊 Class distribution:")
        print(df['maintenance_needed'].value_counts())
        
        return df
    
    def merge_with_real_data(self):
        """Merge Kaggle data with our generated historical data"""
        print("\n🔗 Merging with real equipment data from database...")
        
        try:
            from maintenance.models import EquipmentUsageLog, MaintenanceRecord
            from datetime import timedelta
            
            # Get all usage logs
            usage_logs = EquipmentUsageLog.objects.select_related('equipment', 'booking').all()
            
            if not usage_logs:
                print("⚠️  No usage logs found. Run 'python manage.py generate_historical_data' first!")
                return None
            
            # Convert to DataFrame
            real_data = []
            for log in usage_logs:
                # Check if maintenance was needed within 30 days after this usage
                maintenance_after = MaintenanceRecord.objects.filter(
                    equipment=log.equipment,
                    scheduled_date__gte=log.created_at,
                    scheduled_date__lte=log.created_at + timedelta(days=30)
                ).exists()
                
                real_data.append({
                    'equipment_type': log.equipment.equipment_type.category,
                    'hours_used': float(log.hours_used),
                    'kilometers_covered': float(log.kilometers_covered),
                    'fuel_consumed': float(log.fuel_consumed),
                    'operating_temperature_avg': float(log.operating_temperature_avg or 75),
                    'load_factor': float(log.load_factor),
                    'terrain_type': log.terrain_type,
                    'idle_time_hours': float(log.idle_time_hours),
                    'error_count': log.error_count,
                    'cumulative_hours': log.equipment.total_hours,
                    'cumulative_km': getattr(log.equipment, 'total_kilometers', 0),
                    'maintenance_needed': 1 if maintenance_after else 0
                })
            
            real_df = pd.DataFrame(real_data)
            
            # Save merged data
            output_file = self.data_dir / 'complete_training_data.csv'
            real_df.to_csv(output_file, index=False)
            print(f"✅ Complete training data saved to: {output_file}")
            print(f"   Shape: {real_df.shape}")
            print(f"\n📊 Statistics:")
            print(real_df.describe())
            
            return real_df
            
        except Exception as e:
            print(f"❌ Error merging data: {e}")
            return None


def main():
    """Main execution"""
    print("=" * 60)
    print("🤖 KAGGLE DATASET PREPARATION FOR PREDICTIVE MAINTENANCE")
    print("=" * 60)
    
    prep = KaggleDataPreparation()
    
    # Option 1: Try to download from Kaggle
    print("\n[1] Attempting to download from Kaggle...")
    download_success = prep.download_dataset()
    
    if not download_success:
        # Option 2: Generate synthetic data
        print("\n[2] Generating synthetic data instead...")
        df = prep.generate_synthetic_data(num_records=5000)
    
    # Option 3: Merge with real Django data
    print("\n[3] Attempting to merge with real equipment data...")
    complete_df = prep.merge_with_real_data()
    
    print("\n" + "=" * 60)
    print("✅ DATA PREPARATION COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the generated CSV files in maintenance/data/")
    print("2. Run: python manage.py train_maintenance_model")
    print("3. Generate predictions for your equipment")


if __name__ == '__main__':
    main()