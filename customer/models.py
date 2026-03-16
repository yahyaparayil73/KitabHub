import uuid
from django.db import models
from common.models import Customer,Seller
from seller.models import Product
from django.utils import timezone

# Create your models here.

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE) # Ensure you have a Product model
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        return self.product.p_price * self.quantity
    
    class Meta:
        db_table = 'cart'

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Packed', 'Packed'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
    )

    # We use UUID for the URL to make it secure (SB-XXXXX)
    order_id = models.CharField(max_length=20, unique=True, editable=False,null=True)
    customer = models.ForeignKey('common.Customer', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255,default = 0)
    email = models.EmailField(default = 0)
    shipping_address = models.TextField(default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"KB-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'orders'
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('seller.Product', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2) # Crucial for records

    class Meta:
        db_table = 'order_item'
