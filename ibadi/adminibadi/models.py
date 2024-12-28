from django.db import models
from PIL import Image

# Create your models here.
class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    category_offer_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=int(0))
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    def delete(self,using=None, keep_parents=False):
        self.is_deleted = True
        self.is_active = False
        self.save()

    def restore(self):
        self.is_deleted = False
        self.is_active = True
        self.save()

    class Meta:
        db_table = 'categories'

    def __str__(self):
        return self.category_name
    

   
class ProductVariants(models.Model):
    variant_id = models.AutoField(primary_key=True)
    variant_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    def delete(self,using=None, keep_parents=False):
        self.is_deleted = True
        self.is_active = False
        self.save()

    def restore(self):
        self.is_deleted = False
        self.is_active = True
        self.save()

    class Meta:
        db_table = 'product_variants'

    def __str__(self):
        return self.variant_name



class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=50)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    variant = models.ForeignKey(ProductVariants, on_delete=models.CASCADE, related_name='variants')
    description = models.TextField()
    regular_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_offer_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.product_name
 

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images')
    images = models.ImageField(upload_to='products/')
    is_main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.images.path)
        img = img.resize((500, 500), Image.Resampling.LANCZOS)
        img.save(self.images.path)

    def __str__(self):
        return f'Image for {self.product.product_name}'

    class Meta:
        db_table = 'product_images' 




class Coupon(models.Model):
    coupon_id = models.AutoField(primary_key=True)
    coupon_name = models.CharField(max_length=50, unique=True)
    coupon_code = models.CharField(max_length=20, unique=True)
    expiry_date = models.DateTimeField()
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'coupons'


    def save(self,*args, **kwargs):
        if self.coupon_code:
            self.coupon_code = self.coupon_code.upper()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f'{self.coupon_name} ({self.coupon_code})'



