from django.db import models
from django.contrib.auth.models import AbstractUser
import re
from django.core.exceptions import ValidationError

# 이름 유효성 확인 (미사용 중)
def validate_name(value):
    if not re.match(r'^[ㄱ-힣]{1,4}$', value):  
        raise ValidationError('Name must contain only Korean characters and be 4 characters or fewer.')

class User(AbstractUser):
    first_name = None
    last_name = None
    phone_number = models.CharField(
        max_length=20, 
        blank=False
    )
    name = models.CharField(max_length=4) #, validators=[validate_name]

    def __str__(self):
        return self.name
