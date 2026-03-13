from django.db import models

# Create your models here.

class Customer(models.Model):
    c_name = models.CharField(max_length=100)
    c_email = models.EmailField(unique=True)
    c_phone = models.CharField(max_length=15, unique=True)
    c_password = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customer'

class Seller(models.Model):
    s_name = models.CharField(max_length=100)
    s_email = models.EmailField(unique=True)
    s_store_name = models.CharField(max_length=150, unique=True)
    s_phone = models.CharField(max_length=15)
    s_password = models.CharField(max_length=100)
    
    # Banking details for professional settlements
    s_bank_account = models.CharField(max_length=20, null=True, blank=True)
    s_bank_ifsc = models.CharField(max_length=20, null=True, blank=True)
    s_bank_branch = models.CharField(max_length=100, null=True, blank=True)
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'seller'

class Admin(models.Model):
    a_username = models.CharField(max_length = 50)
    a_password = models.CharField(max_length = 20)

    class Meta:
        db_table = 'admin'

 
    