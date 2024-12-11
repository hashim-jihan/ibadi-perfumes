from django import forms
from .models import User
from django.core.exceptions import ValidationError

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder' : 'Password'}),required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder' : 'Confirm Password'}),required=False)

    class Meta:
        model = User
        fields = ['full_name','email','password']
        widgets = {
            'full_name' :forms.TextInput(attrs={'placeholder' : 'Full Name'}),
            'email' : forms.EmailInput(attrs={'placeholder' : 'Email'})

        }

        error_messages = {
            'full_name': {'required': 'Full Name is required.'},
            'email': {'required': 'Email is required.'},
            'password': {'required': 'Password is required.'},
        }

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not full_name:
            raise ValidationError('Full Name is required ') 
        
        return full_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        existingUser = User.objects.filter(email=email, is_active=False)
        if existingUser:
            existingUser.delete()
            
        if not email:
            raise ValidationError('Email is required')
        if not '@' in email:
            raise ValidationError('Enter a valid email')
        if User.objects.filter(email=email,is_active=True).exists():
            raise ValidationError('Email is already taken')
        
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise ValidationError('Password is required')
        if len(password) < 8:
            raise ValidationError('Password must be 8 characters')
        
        return password
    
    def clean_confirm_password(self):
        confirm_password = self.cleaned_data.get('confirm_password')
        if not confirm_password:
            raise ValidationError('Confirm password is required')
        password = self.cleaned_data.get('password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError('Passwords do not match')
        
        return confirm_password
    
class userLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder' : 'Email Address'}),required=False)
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


   