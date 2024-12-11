from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager
from django.utils.crypto import get_random_string
from datetime import datetime,timedelta
from django.utils.timezone import now
from adminibadi.models import Product


# Create your models here.

class CustomUserManager(BaseUserManager):
    
    def create_user(self,full_name,email,password=None):
        if not email:
            raise ValueError('Must have Email!')
        
        user = self.model(
            email = self.normalize_email(email),
            full_name = full_name

        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self,full_name,email,password=None):
        user = self.create_user(full_name,email,password)
        user.is_admin = True
        user.save(using=self._db)
        return user
    

class User(AbstractBaseUser):
    full_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)  # New field for OTP timestamp


    objects = CustomUserManager()

    class Meta:
        db_table = 'users'

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email
    
    @property
    def is_staff(self):
        return self.is_admin

    def generated_otp(self):
        self.otp = get_random_string(6, allowed_chars='0123456789')
        self.otp_created_at = now()
        self.save()



class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=12)
    address = models.TextField()
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    landmark = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'addresses'

    def __str__(self):
        return f'{self.name}'
    

class Cart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'cart'

    def __str__(self):
        return f'{self.user.name}'
    
    



        
        
