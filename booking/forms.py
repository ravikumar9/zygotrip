from django import forms
from meals.models import MealPlan
from rooms.models import RoomType


class BookingCreateForm(forms.Form):
    room_type = forms.ModelChoiceField(queryset=RoomType.objects.none())
    meal_plan = forms.ModelChoiceField(queryset=MealPlan.objects.none(), required=False)
    check_in = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    check_out = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    quantity = forms.IntegerField(min_value=1, initial=1)
    guest_full_name = forms.CharField(max_length=120)
    guest_age = forms.IntegerField(min_value=1, initial=25)
    guest_email = forms.EmailField(required=False)
    promo_code = forms.CharField(max_length=20, required=False)

    def __init__(self, *args, **kwargs):
        property_obj = kwargs.pop('property_obj', None)
        super().__init__(*args, **kwargs)
        if property_obj:
            self.fields['room_type'].queryset = property_obj.room_types.filter(is_active=True)
            self.fields['meal_plan'].queryset = property_obj.meal_plans.filter(is_active=True)
