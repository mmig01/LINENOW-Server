import random
import string
from django.db import models
from booth.models import Booth
from accounts.models import User

# Create your models here.
# FAQ
class FAQ(models.Model):
    faq_id = models.AutoField(primary_key=True)
    question = models.CharField(max_length=100)
    answer = models.TextField()

# Admin 계정, code는 unique하게 설정, name은 부스와 1:1 대응
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null =  True)  # User 모델과 1:1 관계
    admin_code = models.CharField(max_length=255, unique=True)
    booth = models.OneToOneField(Booth, on_delete=models.CASCADE, related_name='admin')

    def __str__(self):
        return f'{self.booth.name} 관리자'
    
    def save(self, *args, **kwargs):
        # 새로운 Admin 객체일 때, User 객체도 생성
        if not self.pk:
            # 랜덤한 비밀번호 생성
            random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

            # User 객체 생성 (username은 admin_code 기반, 비밀번호는 랜덤)
            user = User.objects.create_user(
                username=f"admin_{self.booth.name}",
                password=random_password  # 랜덤 비밀번호 설정
            )
            self.user = user
        
        if not self.admin_code:  # 고유번호가 없으면 생성
            self.admin_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))  # 8자리 랜덤 고유번호 생성

        super().save(*args, **kwargs)