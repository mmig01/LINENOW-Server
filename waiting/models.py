from django.db import models
from django.utils import timezone
from booth.models import Booth

from accounts.models import User

class Waiting(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'waiting'),
        ('canceled', 'canceled'),
        ('entered', 'entered'),
        ('entering', 'entering'),
        ('not_waiting', 'not_waiting'),
        ('time_over', 'time_over')
    ]
    
    waiting_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='waitings')  # 사용자
    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name='waitings')
    person_num = models.IntegerField(verbose_name="인원 수")
    
    waiting_num = models.IntegerField(verbose_name="대기 번호")
    waiting_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting', verbose_name="대기 상태")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="대기 생성 시간")  # 웨이팅 등록 시간을 위한 필드 추가 !!
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="대기 호출 시간")
    canceled_at = models.DateTimeField(null=True, blank=True, verbose_name="대기 취소 시간")
    arrived_at = models.CharField(max_length=10, null=True, blank=True, verbose_name="입장 시간")
    notified_at = models.DateTimeField(null=True, blank=True)
    
    # created_at = models.DateTimeField(auto_now_add=True, verbose_name="대기 생성 시간")
    # updated_at = models.DateTimeField(auto_now=True, verbose_name="대기 업데이트 시간")
    
    def __str__(self):
        return f'Waiting {self.waiting_id} - {self.booth.booth_name} - {self.user.user_name}'
    
    def save(self, *args, **kwargs):
        if self.waiting_status == 'entered' and self.confirmed_at:
            if not self.arrived_at:
                # 현재 시간과 confirmed_at의 차이를 계산
                time_diff = timezone.now() - self.confirmed_at
                minutes = time_diff.seconds // 60  # 분 단위
                seconds = time_diff.seconds % 60  # 초 단위
                self.arrived_at = f"{minutes:02d}-{seconds:02d}"  # "00-00" 형식으로 저장

        super().save(*args, **kwargs)
    
    # def set_ready_to_confirm(self):
    #     """호출 후 ready_to_confirm 상태로 전환 및 Celery 작업 호출"""
    #     self.waiting_status = 'ready_to_confirm'
    #     self.ready_to_confirm_at = timezone.now()
    #     self.save()
    #     # 3분 후 상태 확인 작업 호출
    #     check_ready_to_confirm.apply_async((self.id,), countdown=180)

    # def set_confirmed(self):
    #     """입장 확정 후 confirmed 상태로 전환 및 Celery 작업 호출"""
    #     self.waiting_status = 'confirmed'
    #     self.confirmed_at = timezone.now()
    #     self.save()
        
    # def set_time_over_canceled(self):
    #     """3분 내에 입장 확정하지 않을 시 시간 초과로 인한 대기 취소"""
    #     self.waiting_status = 'time_over_canceled'
    #     self.canceled_at = timezone.now()
    #     self.save()

    # def set_canceled(self):
    #     """대기 취소 상태로 변경"""
    #     self.waiting_status = 'canceled'
    #     self.canceled_at = timezone.now()
    #     self.save()

    # def is_ready_to_confirm_expired(self):
    #     """3분 이내에 입장 확정 여부 확인"""
    #     return self.ready_to_confirm_at and (timezone.now() - self.ready_to_confirm_at).total_seconds() > 180

    # def is_confirmed_expired(self):
    #     """10분 이내에 도착 여부 확인"""
    #     return self.confirmed_at and (timezone.now() - self.confirmed_at).total_seconds() > 600