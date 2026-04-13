# core/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Patient

class RegisterForm(forms.Form):
    ROLE_CHOICES = [('patient', 'Patient'), ('doctor', 'Doctor')]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect, initial='patient')
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    phone = forms.CharField(max_length=10)
    age = forms.IntegerField(min_value=1, max_value=120)
    gender = forms.ChoiceField(choices=[
        ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')
    ])
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    # Doctor-only fields
    specialization = forms.CharField(max_length=100, required=False)
    qualification = forms.CharField(max_length=200, required=False)
    experience = forms.IntegerField(min_value=0, required=False)
    fee = forms.IntegerField(min_value=0, required=False)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Email already registered!")
        return email