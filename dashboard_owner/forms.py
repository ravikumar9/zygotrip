from django import forms
from django.core.exceptions import ValidationError
from apps.hotels.validators import validate_https_image_url
from hotels.models import Property, PropertyImage, PropertyOffer, RatingAggregate, Category, PropertyCategory
from meals.models import MealPlan
from rooms.models import RoomType, RoomImage


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'property_type', 'city', 'area', 'landmark', 'country', 'address', 'description', 'rating', 'latitude', 'longitude']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001'}),
        }


class PropertyImageForm(forms.ModelForm):
    """Form for uploading property images with validation"""
    class Meta:
        model = PropertyImage
        fields = ['image_url', 'caption', 'is_featured', 'display_order']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Optional: Describe this image'}),
            'display_order': forms.NumberInput(attrs={'min': 0, 'value': 0}),
        }
    
    def clean_image_url(self):
        url = self.cleaned_data.get('image_url')
        if url:
            validate_https_image_url(url)
        return url
    
    def clean(self):
        cleaned_data = super().clean()
        # Auto-unset other featured images when is_featured is True
        if cleaned_data.get('is_featured'):
            property_obj = getattr(self.instance, 'property', None)
            if property_obj:
                PropertyImage.objects.filter(property=property_obj, is_featured=True).update(is_featured=False)
        return cleaned_data


class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['name', 'description', 'base_price', 'max_guests', 'bed_type', 'room_size_sqm']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class RoomImageForm(forms.ModelForm):
    """Form for uploading room images"""
    class Meta:
        model = RoomImage
        fields = ['image_url', 'is_featured', 'display_order']
    
    def clean_image_url(self):
        url = self.cleaned_data.get('image_url')
        if url:
            validate_https_image_url(url)
        return url


class MealPlanForm(forms.ModelForm):
    class Meta:
        model = MealPlan
        fields = ['name', 'meal_type', 'description', 'price', 'icon']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'icon': forms.TextInput(attrs={'placeholder': 'e.g., 🍳 or fa-utensils'}),
        }


class PropertyOfferForm(forms.ModelForm):
    """Form for creating promotional offers"""
    class Meta:
        model = PropertyOffer
        fields = ['title', 'description', 'discount_percentage', 'discount_amount', 'valid_from', 'valid_until', 'is_active', 'code']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'valid_from': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
            'code': forms.TextInput(attrs={'placeholder': 'e.g., SUMMER2024'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        discount_pct = cleaned_data.get('discount_percentage')
        discount_amt = cleaned_data.get('discount_amount')
        
        if not discount_pct and not discount_amt:
            raise ValidationError('Either discount percentage or discount amount must be provided')

        if discount_pct and discount_pct > 90:
            raise ValidationError('Discount percentage must be 90 or less')
        
        valid_from = cleaned_data.get('valid_from')
        valid_until = cleaned_data.get('valid_until')
        
        if valid_from and valid_until and valid_from >= valid_until:
            raise ValidationError('Valid from date must be before valid until date')
        
        return cleaned_data


class RatingAggregateForm(forms.ModelForm):
    """Form for updating rating breakdowns"""
    class Meta:
        model = RatingAggregate
        fields = ['cleanliness', 'service', 'location', 'amenities', 'value_for_money', 'total_reviews']
        widgets = {
            'cleanliness': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '5'}),
            'service': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '5'}),
            'location': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '5'}),
            'amenities': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '5'}),
            'value_for_money': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '5'}),
        }

class PriceForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['base_price']
