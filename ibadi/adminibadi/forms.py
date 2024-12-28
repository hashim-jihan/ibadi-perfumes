from django import forms
from django.core.exceptions import ValidationError
from datetime import date

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
    


class CouponForm(forms.Form):
    coupon_code = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={ 'class':'form-control'}))
    coupon_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={ 'class':'form-control'}))
    discount_percentage = forms.FloatField(required=True, min_value=0, max_value=100, widget=forms.NumberInput(attrs={ 'class':'form-control'}))
    minimum_purchase = forms.FloatField(required=True, min_value=0, widget=forms.NumberInput(attrs={ 'class':'form-control'}))
    maximum_discount = forms.FloatField(required=True, min_value=0, widget=forms.NumberInput(attrs={ 'class':'form-control'}))
    expiry_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type':'date', 'class':'form-control'}))


    def clean_coupon_code(self):
        coupon_code = self.cleaned_data.get('coupon_code')
        if len(coupon_code) < 5:
            raise forms.ValidationError('Coupon code must be at least 5 characters')
        return coupon_code


    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        if expiry_date < date.today():
            raise forms.ValidationError('Expiry date must be in the future')
        return expiry_date



