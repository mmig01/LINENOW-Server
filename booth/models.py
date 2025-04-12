from django.db import models
from django.utils import timezone
# Create your models here.
def image_upload_path(instance, filename):
    booth_id = instance.booth.booth_id
    return f'booth_{booth_id}/{filename}'

class Festival(models.Model):
    id = models.AutoField(primary_key=True)
    fastival_name = models.CharField(max_length=100, verbose_name="행사명")
    
    def __str__(self):
        return self.fastival_name
    
class Booth(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'not_started'), # DB에 저장되는 값, 사용자에게 보여지는 값 순
        ('operating', 'operating'),
        ('finished', 'finished'),
        ('paused', 'paused')
    ]

    booth_id = models.AutoField(primary_key=True)
    booth_name = models.CharField(max_length=100, verbose_name="부스명")
    booth_description = models.TextField(verbose_name="부스 설명")
    booth_location = models.CharField(max_length=255, verbose_name="부스 위치")
    booth_start_time = models.DateTimeField(verbose_name="운영 시작 시간")
    booth_end_time = models.DateTimeField(verbose_name="운영 마감 시간")
    booth_notice = models.TextField(verbose_name="부스 공지")
    booth_latitude = models.CharField(max_length=255, verbose_name="부스 위치 위도")
    booth_longitude = models.CharField(max_length=255, verbose_name="부스 위치 경도")
    operating_status = models.CharField(max_length=100, choices=STATUS_CHOICES, verbose_name="부스 운영 상태")
    current_watiting_num = models.IntegerField(verbose_name="최신 대기 번호")

    def __str__(self):
        return self.booth_name
    
class BoothMenu(models.Model):
    menu_id = models.AutoField(primary_key=True)
    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name="booth_menus")
    menu_name = models.CharField(max_length=100, verbose_name="메뉴 이름")
    menu_price = models.IntegerField(verbose_name="메뉴 가격")

    def __str__(self):
        return f'{self.menu_name} - {int(self.menu_price):,}원'
    
class BoothImage(models.Model):
    booth_image_id = models.AutoField(primary_key=True)
    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name="booth_images")
    booth_image = models.ImageField(upload_to=image_upload_path, blank=True, null=True, verbose_name="사진")
    
    def __str__(self):
        return f'{self.booth.booth_name} - {self.booth_image_id}'