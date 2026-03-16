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
    # Status Choices for the Admin "Protocol" column
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Transit', 'In Transit'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    customer = models.ForeignKey('common.Customer', on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey('seller.Product', on_delete=models.CASCADE, related_name='ordered_product')
    seller = models.ForeignKey('common.Seller', on_delete=models.CASCADE, related_name='seller_orders')
    o_quantity = models.PositiveIntegerField(default=1)
    o_total_price = models.DecimalField(max_digits=12, decimal_places=2) # e.g. 10000.00
    o_date = models.DateTimeField(default=timezone.now)
    o_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    o_address_snapshot = models.TextField() # Keeps the address even if customer changes profile later
    o_transaction_id = models.CharField(max_length=100, unique=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.c_name}"

    class Meta:
        db_table = 'orders'


# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField(default=1)
#     price = models.DecimalField(max_digits=10, decimal_places=2)  # Unit price
#     subtotal = models.DecimalField(max_digits=10, decimal_places=2)

#     def save(self, *args, **kwargs):
#         self.subtotal = self.quantity * self.price
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.product.title} (x{self.quantity})"
