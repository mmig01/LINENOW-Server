from celery import shared_task
from django.utils import timezone

@shared_task
def check_ready_to_confirm(waiting_id):
    """3분 후 ready_to_confirm 상태에서 입장 확정되지 않았으면 시간 초과로 취소"""
    from .models import Waiting
    try:
        waiting = Waiting.objects.get(pk=waiting_id)
        # 3분이 지났으면 확인하고 취소 처리
        if waiting.is_ready_to_confirm_expired() and waiting.waiting_status == 'ready_to_confirm':
            waiting.set_time_over_canceled()  # 시간 초과로 취소 처리
    except Waiting.DoesNotExist:
        pass

@shared_task
def check_confirmed(waiting_id):
    """10분 후 입장 확정 상태에서 도착하지 않으면 취소"""
    from .models import Waiting
    try:
        waiting = Waiting.objects.get(pk=waiting_id)
        # 10분이 지났으면 취소 처리
        if waiting.is_confirmed_expired():
            waiting.set_canceled()  # 대기 취소 처리
    except Waiting.DoesNotExist:
        pass