from django.core.management.base import BaseCommand
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')


class Command(BaseCommand):
    help = 'Train ML model for predictive maintenance'
    
    def __init__(self):
        super().__init__()
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_dir / 'data'
        self.models_dir = self.base_dir / 'ml_models'
        self.models_dir.mkdir(exist_ok=True)
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            '\n' + '='*60 + '\n'
            '🤖 TRAINING PREDICTIVE MAINTENANCE MODEL\n'
            + '='*60 + '\n'
        ))
        
        # Step 1: Load data
        df = self.load_training_data()
        if df is None:
            return
        
        # Step 2: Prepare features
        X, y_failure, y_days = self.prepare_features(df)
        
        # Step 3: Train failure prediction model
        failure_model = self.train_failure_model(X, y_failure)
        
        # Step 4: Train days-until-maintenance model
        days_model = self.train_days_model(X, y_days)
        
        # Step 5: Save models
        self.save_models(failure_model, days_model)
        
        self.stdout.write(self.style.SUCCESS(
            '\n✅ Training complete! Models saved to maintenance/ml_models/\n'
        ))
    
    def load_training_data(self):
        """Load training data from CSV"""
        self.stdout.write('📂 Loading training data...')
        
        # Try different data sources
        possible_files = [
            self.data_dir / 'complete_training_data.csv',
            self.data_dir / 'synthetic_maintenance_data.csv',
        ]
        
        for file_path in possible_files:
            if file_path.exists():
                df = pd.read_csv(file_path)
                self.stdout.write(self.style.SUCCESS(
                    f'   ✅ Loaded {len(df)} records from {file_path.name}'
                ))
                return df
        
        self.stdout.write(self.style.ERROR(
            '   ❌ No training data found!\n'
            '   Please run: python maintenance/ml_utils/prepare_kaggle_data.py\n'
        ))
        return None
    
    def prepare_features(self, df):
        """Prepare features for training"""
        self.stdout.write('\n🔧 Preparing features...')
        
        # Encode categorical variables
        if 'terrain_type' in df.columns:
            le_terrain = LabelEncoder()
            df['terrain_encoded'] = le_terrain.fit_transform(df['terrain_type'])
            joblib.dump(le_terrain, self.models_dir / 'terrain_encoder.pkl')
        
        if 'equipment_type' in df.columns:
            le_equipment = LabelEncoder()
            df['equipment_encoded'] = le_equipment.fit_transform(df['equipment_type'])
            joblib.dump(le_equipment, self.models_dir / 'equipment_encoder.pkl')
        
        # Feature engineering
        df['fuel_efficiency'] = df['kilometers_covered'] / (df['fuel_consumed'] + 1)
        df['hours_per_km'] = df['hours_used'] / (df['kilometers_covered'] + 1)
        df['utilization_rate'] = (df['hours_used'] - df.get('idle_time_hours', 0)) / (df['hours_used'] + 1)
        
        # Select features
        feature_columns = [
            'hours_used', 
            'kilometers_covered', 
            'fuel_consumed',
            'operating_temperature_avg', 
            'load_factor',
            'error_count', 
            'cumulative_hours', 
            'cumulative_km',
            'fuel_efficiency',
            'hours_per_km',
            'utilization_rate'
        ]
        
        # Add optional columns
        if 'idle_time_hours' in df.columns:
            feature_columns.append('idle_time_hours')
        if 'terrain_encoded' in df.columns:
            feature_columns.append('terrain_encoded')
        if 'equipment_encoded' in df.columns:
            feature_columns.append('equipment_encoded')
        if 'days_since_last_maintenance' in df.columns:
            feature_columns.append('days_since_last_maintenance')
        
        # Get available features
        available_features = [col for col in feature_columns if col in df.columns]
        X = df[available_features].fillna(0)
        
        # Target variables
        y_failure = df['maintenance_needed'].fillna(0)
        
        # Calculate days until maintenance
        if 'days_since_last_maintenance' in df.columns:
            y_days = df.apply(
                lambda row: max(1, int(30 * (1 - row['maintenance_needed']) + np.random.uniform(-5, 5))), 
                axis=1
            )
        else:
            y_days = df.apply(
                lambda row: max(1, int(90 * (1 - row['maintenance_needed']) + np.random.uniform(-10, 10))), 
                axis=1
            )
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=available_features)
        
        # Save scaler and feature names
        joblib.dump(scaler, self.models_dir / 'feature_scaler.pkl')
        joblib.dump(available_features, self.models_dir / 'feature_names.pkl')
        
        self.stdout.write(self.style.SUCCESS(
            f'   ✅ Prepared {len(available_features)} features'
        ))
        self.stdout.write(f'   📋 Features: {", ".join(available_features)}')
        
        return X_scaled, y_failure, y_days
    
    def train_failure_model(self, X, y):
        """Train failure prediction model"""
        self.stdout.write('\n🎯 Training failure prediction model...')
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if y.sum() > 0 else None
        )
        
        # Train Random Forest
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.stdout.write(self.style.SUCCESS(
            f'   ✅ Model trained! Accuracy: {accuracy:.2%}'
        ))
        
        # Show report
        if len(set(y_test)) > 1:
            self.stdout.write('\n   📊 Classification Report:')
            report = classification_report(y_test, y_pred)
            for line in report.split('\n'):
                if line.strip():
                    self.stdout.write(f'      {line}')
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        self.stdout.write('\n   🔝 Top 5 Important Features:')
        for idx, row in feature_importance.head(5).iterrows():
            self.stdout.write(f'      {row["feature"]}: {row["importance"]:.4f}')
        
        return model
    
    def train_days_model(self, X, y):
        """Train days-until-maintenance prediction model"""
        self.stdout.write('\n📅 Training days-until-maintenance model...')
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train Random Forest Regressor
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        self.stdout.write(self.style.SUCCESS(
            f'   ✅ Model trained!\n'
            f'      MAE: {mae:.2f} days\n'
            f'      RMSE: {rmse:.2f} days'
        ))
        
        return model
    
    def save_models(self, failure_model, days_model):
        """Save trained models"""
        self.stdout.write('\n💾 Saving models...')
        
        joblib.dump(failure_model, self.models_dir / 'failure_prediction_model.pkl')
        joblib.dump(days_model, self.models_dir / 'days_prediction_model.pkl')
        
        self.stdout.write(self.style.SUCCESS(
            f'   ✅ Models saved to {self.models_dir}/'
        ))
        
        # Save metadata
        import json
        from django.utils import timezone
        metadata = {
            'model_version': 'v1.0',
            'trained_date': timezone.now().isoformat(),
            'failure_model': 'RandomForestClassifier',
            'days_model': 'RandomForestRegressor'
        }
        
        with open(self.models_dir / 'model_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)