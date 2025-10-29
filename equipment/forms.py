from django import forms
from .models import Equipment


class EquipmentForm(forms.ModelForm):
    specifications = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        help_text='Optional JSON, e.g. {"power":"80 HP","width":"2.5m"}'
    )
    features = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='Optional JSON array, e.g. ["4WD","AC Cabin"]'
    )

    class Meta:
        model = Equipment
        fields = [
            'name', 'equipment_type', 'description', 'model', 'year_manufactured',
            'condition', 'status', 'main_image', 'daily_rate', 'hourly_rate',
            'weekly_rate', 'monthly_rate', 'fuel_type', 'fuel_consumption',
            'capacity', 'city', 'country',
            'minimum_booking_hours', 'maximum_booking_days', 'is_active',
            'specifications', 'features'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'equipment_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'year_manufactured': forms.NumberInput(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'daily_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'weekly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'monthly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'fuel_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'capacity': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'minimum_booking_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'maximum_booking_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set sensible defaults for quicker listing visibility
        if not self.instance or not self.instance.pk:
            self.fields['status'].initial = 'available'
            self.fields['is_active'].initial = True

    def clean_specifications(self):
        import json
        data = self.cleaned_data.get('specifications')
        if not data:
            return {}
        try:
            return json.loads(data)
        except Exception:
            raise forms.ValidationError('Invalid JSON for specifications.')

    def clean_features(self):
        import json
        data = self.cleaned_data.get('features')
        if not data:
            return []
        try:
            return json.loads(data)
        except Exception:
            raise forms.ValidationError('Invalid JSON for features.')
