from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'full_name', 'password1', 'password2']

    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    full_name = forms.CharField(max_length=120, widget=forms.TextInput(attrs={'placeholder': 'Full name'}))

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class CustomAuthenticationForm(AuthenticationForm):
    """Authentication form for custom User model with email as primary field"""
    username = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
            'autofocus': True,
            'required': True
        })
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        })
    )
    
    def clean_username(self):
        """Normalize email on login"""
        username = self.cleaned_data.get('username', '').strip().lower()
        return username
