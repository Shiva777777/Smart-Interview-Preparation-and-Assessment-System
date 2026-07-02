from django.db import models
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control form-control-custom', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control form-control-custom', 'placeholder': 'Confirm Password'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-custom', 'placeholder': 'Phone Number'}))
    preferred_domain = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-custom', 'placeholder': 'Preferred Domain'}))
    career_goal = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-custom', 'placeholder': 'Career Goal'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control form-control-custom', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-custom', 'placeholder': 'Email Address'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-custom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-custom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-custom'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'preferred_domain', 'career_goal', 'bio']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control form-control-custom'}),
            'preferred_domain': forms.TextInput(attrs={'class': 'form-control form-control-custom', 'placeholder': 'e.g. Civil Engineering, Python Developer'}),
            'career_goal': forms.TextInput(attrs={'class': 'form-control form-control-custom', 'placeholder': 'e.g. Civil Engineer, Backend Developer'}),
            'bio': forms.Textarea(attrs={'class': 'form-control form-control-custom', 'rows': 3}),
        }
