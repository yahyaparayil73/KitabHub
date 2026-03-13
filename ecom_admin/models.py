from django.db import models

#Create your models here.

class Users(models.Model):
    name = models.CharField(max_length=20)
    email = models.CharField(max_length=40)
    password = models.CharField(max_length=25)
    age = models.IntegerField()
    phone_number = models.BigIntegerField()
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    address = models.TextField()



 

