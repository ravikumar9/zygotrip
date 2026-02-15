from django import forms
from hotels.models import Property
from meals.models import MealPlan
from rooms.models import RoomType


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'city', 'country', 'address', 'description', 'rating']


class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['name', 'description', 'base_price', 'max_guests']


class MealPlanForm(forms.ModelForm):
    class Meta:
        model = MealPlan
        fields = ['name', 'price']


class PriceForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['base_price']
