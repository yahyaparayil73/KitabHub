from django.db import models
from common.models import Seller,Customer

# Create your models here.


class Product(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    p_name = models.CharField(max_length=250)
    p_description = models.CharField(max_length=250)
    p_author = models.CharField(max_length=100)
    p_number = models.BigIntegerField()
    p_stock = models.BigIntegerField()
    p_price = models.DecimalField(max_digits=5, decimal_places=2)
    p_genre = models.CharField(max_length=100, blank=True, null=True)
    best_seller = models.CharField(max_length=50, blank=True, null=True)
    p_image = models.ImageField(upload_to='product/')
    p_year = models.CharField(max_length=50)

    class Meta: 
        db_table = 'Product'
