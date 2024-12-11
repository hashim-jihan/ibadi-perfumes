from django import forms
from django.core.exceptions import ValidationError

class aloginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder' : 'Admin Email'}),required=False)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder' : 'Password'}),required=False)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('Email is required')
        
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise ValidationError('Password is required')
        
        return password
