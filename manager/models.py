import random
import string
from django.db import models
from booth.models import Booth

# Create your models here.
# FAQ
class FAQ(models.Model):
    faq_id = models.AutoField(primary_key=True)
    question = models.CharField(max_length=100)
    answer = models.TextField()

# Admin 계정, code는 unique하게 설정, name은 후에 부스와 1:1 대응 예정
class Admin(models.Model):
    admin_code = models.CharField(max_length=255, unique=True)
    booth = models.OneToOneField(Booth, on_delete=models.CASCADE, related_name='admin')

    def __str__(self):
        return f'{self.booth.name} 관리자'
    
    def save(self, *args, **kwargs):
        if not self.admin_code:  # 고유번호가 없으면 생성
            self.admin_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))  # 8자리 랜덤 고유번호 생성
        super().save(*args, **kwargs)