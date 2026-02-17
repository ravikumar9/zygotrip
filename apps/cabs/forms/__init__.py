from django import forms


class CabFilterForm(forms.Form):
	q = forms.CharField(required=False)
	city = forms.MultipleChoiceField(required=False)
	seats = forms.MultipleChoiceField(required=False)
	fuel_type = forms.MultipleChoiceField(required=False)
	min_price = forms.DecimalField(required=False, min_value=0)
	max_price = forms.DecimalField(required=False, min_value=0)
