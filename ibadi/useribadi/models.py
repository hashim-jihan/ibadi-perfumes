from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin
from django.utils.crypto import get_random_string
from datetime import datetime,timedelta
from django.utils.timezone import now
from adminibadi.models import Product,Coupon
from decimal import Decimal
import uuid


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
        user.is_superuser = True
        user.save(using=self._db)
        return user
    


class User(AbstractBaseUser, PermissionsMixin):
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



class ShippingAddress(models.Model):
    shipping_address_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name='shipping_addresses')
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=12)
    address = models.TextField()
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    landmark = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'shipping_addresses'



class Order(models.Model):

    order_status_choices = [
        ('PENDING', 'pending'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),


    ]

    payment_method_choices = [
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment'),
        ('WALLET', 'Wallet Payment')
    ]

    payment_status_choices = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
    ]

    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=payment_method_choices)
    payment_status = models.CharField(max_length=20, choices=payment_status_choices, default='PENDING')
    order_at = models.DateField(auto_now_add=True)
    order_status = models.CharField(max_length=50,choices=order_status_choices,default='pending')
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE)
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=50, null=True, blank=True)
    return_reason = models.TextField(blank=True,null=True)

    def save(self,*args, **kwargs):
        if not self.original_amount:
            self.original_amount = self.final_amount
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'orders'


    def __str__(self):
        return f'Order {self.order_id}  {self.user.full_name}'



class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_cancelled = models.BooleanField(default=False)
    discounted_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        db_table = 'order_items'



class Wishlist(models.Model):
    wishlist_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)


    class Meta:
        db_table = 'wishlist'

    def __str__(self):
        return f'{self.user.full_name} wishlist: {self.Product.product_name}'



class Wallet(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('CREDITED', 'Credited'),
        ('DEBITED', 'Debited'),
    ]
    wallet_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, default=TRANSACTION_TYPE_CHOICES)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        if self.transaction_type == 'Credited':
            self.current_balance += self.amount
        elif self.transaction_type == 'Debited':
            self.current_balance -= self.amount


        if self.current_balance < Decimal(0.00):
            raise ValueError('Wallet amount cannot be negative value')
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'wallet'
        ordering = ['-created_at']

    def __str__(self):
        return f'Wallet {self.wallet_id} for {self.user.full_name}'    

    

class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=50, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment'

    def __str__(self):
        return {self.user.full_name}

    


    
    



        
        