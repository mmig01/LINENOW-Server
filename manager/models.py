from django.db import models

# Create your models here.
# FAQ
class FAQ(models.Model):
    faq_id = models.AutoField(primary_key=True)
    question = models.CharField(max_length=100)
    answer = models.TextField()

# Admin 계정, code는 unique하게 설정, name은 후에 부스와 1:1 대응 예정
class Admin(models.Model):
    admin_code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
