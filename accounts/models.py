from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    first_name = None
    last_name = None
    password = None
    phone_number = models.CharField(max_length=20, blank=False, name="phone_number")
    nickname = models.CharField(max_length=20, blank=False, name="nickname")