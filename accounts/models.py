from django.db import models
from django.contrib.auth.models import AbstractUser
import re
from django.core.exceptions import ValidationError

# 한글만 허용하고 4글자 이하인지 검사하는 함수
def validate_username(value):
    if not re.match(r'^[ㄱ-힣]{1,4}$', value):  # 1~4글자의 한글만 허용
        raise ValidationError('Username must contain only Korean characters and be 4 characters or fewer.')

class User(AbstractUser):
    first_name = None
    last_name = None
    phone_number = models.CharField(max_length=20, blank=False)
    username = models.CharField(
        max_length=4,  # 최대 4글자
        unique=True,
        validators=[validate_username],  # 유효성 검사 추가
        error_messages={
            'unique': "A user with that username already exists.",
        }
    )

    def __str__(self):
        return self.username
