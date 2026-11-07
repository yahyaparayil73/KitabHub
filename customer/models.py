import uuid
from django.db import models
from common.models import Customer
from seller.models import Product


class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    # Allows payment confirmation to leave later cart edits untouched.
    updated_at = models.DateTimeField(auto_now=True, null=True)

    @property
    def total_price(self):
        return self.product.p_price * self.quantity

    class Meta:
        db_table = 'cart'


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'), ('Packed', 'Packed'), ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'), ('Delivered', 'Delivered'),
    )
    PAYMENT_CHOICES = (
        ('Legacy', 'Legacy order'), ('Initializing', 'Preparing payment'),
        ('Pending', 'Awaiting payment'), ('Paid', 'Payment confirmed'),
        ('Failed', 'Payment could not be started'), ('Expired', 'Checkout expired'),
        ('Review', 'Payment received; order requires review'),
    )
    order_id = models.CharField(max_length=20, unique=True, editable=False, null=True)
    customer = models.ForeignKey('common.Customer', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, default='')
    email = models.EmailField(default='')
    shipping_address = models.TextField(default='')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    checkout_token = models.UUIDField(unique=True, null=True, blank=True, editable=False)
    # Legacy is intentional: old unpaid orders have no trustworthy frozen cart.
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='Legacy')
    reservation_expires_at = models.DateTimeField(null=True, blank=True)
    stock_reserved = models.BooleanField(default=False)
    review_reason = models.CharField(max_length=255, blank=True, default='')

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f'KB-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'orders'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('seller.Product', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    product_name = models.CharField(max_length=255, blank=True, default='')
    product_author = models.CharField(max_length=255, blank=True, default='')
    source_cart_id = models.BigIntegerField(null=True, blank=True)
    source_cart_updated_at = models.DateTimeField(null=True, blank=True)

    @property
    def display_name(self):
        return self.product_name or (self.product.p_name if self.product else 'Book unavailable')

    @property
    def display_author(self):
        return self.product_author or (self.product.p_author if self.product else '')

    @property
    def line_total(self):
        return self.price_at_purchase * self.quantity

    class Meta:
        db_table = 'order_item'
