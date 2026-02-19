# packages/forms.py - Package booking forms with date validation

from django import forms
from django.core.exceptions import ValidationError
from core.date_utils import get_date_for_template, validate_booking_date
from .models import PackageBooking, Package, PackageCategory


class PackageRegistrationForm(forms.ModelForm):
    """Form for package providers to register their packages"""
    
    class Meta:
        model = Package
        fields = ['name', 'destination', 'duration_days', 'base_price', 'description', 
                  'category', 'inclusions', 'exclusions', 'max_group_size', 'difficulty_level', 'image_url']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Goa Beach Paradise'
            }),
            'destination': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Main destination'
            }),
            'duration_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '30'
            }),
            'base_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '₹',
                'step': '0.01',
                'min': '1'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your package'
            }),
            'inclusions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Comma-separated: Hotel, Meals, Transport'
            }),
            'exclusions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Comma-separated: Flight, Insurance'
            }),
            'max_group_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100'
            }),
            'difficulty_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/image.jpg'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make category optional since view provides default
        self.fields['category'].required = False
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError("Package name is required")
        if len(name) < 5:
            raise ValidationError("Package name must be at least 5 characters")
        return name
    
    def clean_base_price(self):
        price = self.cleaned_data.get('base_price')
        if not price or price <= 0:
            raise ValidationError("Price must be greater than ₹0")
        if price < 500:
            raise ValidationError("Minimum price is ₹500")
        if price > 500000:
            raise ValidationError("Price exceeds maximum allowed (₹5,00,000)")
        return price
    
    def clean_duration_days(self):
        days = self.cleaned_data.get('duration_days')
        if not days or days <= 0:
            raise ValidationError("Duration must be at least 1 day")
        if days > 30:
            raise ValidationError("Maximum duration is 30 days")
        return days


class PackageBookingForm(forms.ModelForm):
    """Form for creating package bookings with date validation"""
    
    class Meta:
        model = PackageBooking
        fields = ['start_date', 'end_date', 'promo_code', 'number_of_travellers']
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
        }),
        label='Start Date'
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
        }),
        label='End Date'
    )
    promo_code = forms.CharField(
        max_length=30,
        required=False,
        label='Promo Code'
    )
    number_of_travellers = forms.IntegerField(
        min_value=1,
        initial=1,
        label='Number of Travellers'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set minimum date for date fields
        today = get_date_for_template()
        self.fields['start_date'].widget.attrs['min'] = today
        self.fields['end_date'].widget.attrs['min'] = today
    
    def clean_start_date(self):
        """Backend validation for start date"""
        start_date = self.cleaned_data.get('start_date')
        if start_date:
            valid, message = validate_booking_date(start_date, allow_today=True)
            if not valid:
                raise ValidationError(message)
        return start_date
    
    def clean_end_date(self):
        """Backend validation for end date"""
        end_date = self.cleaned_data.get('end_date')
        if end_date:
            valid, message = validate_booking_date(end_date, allow_today=True)
            if not valid:
                raise ValidationError(message)
        return end_date
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError("End date must be after start date")
            
            # Validate duration (not more than 30 days)
            duration = (end_date - start_date).days
            if duration > 30:
                raise ValidationError("Package duration cannot exceed 30 days")
        
        return cleaned_data


class PackageBookingCreateForm(PackageBookingForm):
    """Booking form with traveler details"""

    traveler_full_name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Traveler Name'
    )
    traveler_age = forms.IntegerField(
        min_value=1,
        max_value=120,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Traveler Age'
    )
    traveler_relationship = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Relationship (Optional)'
    )
    traveler_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Email (Optional)'
    )
    traveler_phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Phone (Optional)'
    )
