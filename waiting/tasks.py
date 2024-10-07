from celery import shared_task
from django.utils import timezone
from utils.sendmessages import sendsms

@shared_task
def check_ready_to_confirm(waiting_id):
    """3분 후 ready_to_confirm 상태에서 입장 확정되지 않았으면 시간 초과로 취소"""
    from .models import Waiting
    try:
        waiting = Waiting.objects.get(pk=waiting_id)
        # 3분이 지났으면 확인하고 취소 처리
        if waiting.is_ready_to_confirm_expired() and waiting.waiting_status == 'ready_to_confirm':
            waiting.set_time_over_canceled()  # 시간 초과로 취소 처리
            # 문자 메시지 발송
            phone_number = waiting.user.phone_number
            print(phone_number)
            sendsms(phone_number, f"[대기취소] 3분 내에 부스 입장을 확정하지 않아, 대기가 취소되었어요")
    except Waiting.DoesNotExist:
        pass

@shared_task
def check_confirmed(waiting_id, phone_number):
    print("기다림은 끝")
    """10분 후 입장 확정 상태에서 도착하지 않으면 time_over_canceled 상태로 변경"""
    from .models import Waiting
    try:
        print("데이터가져와")
        waiting = Waiting.objects.get(pk=waiting_id)
        # 10분이 지났으면 취소 처리
        if waiting.is_confirmed_expired() and waiting.waiting_status == 'confirmed':
            waiting.set_time_over_canceled()  # 시간 초과로 취소 처리
            # 문자 메시지 발송
            print(phone_number)
            sendsms(phone_number, f"[대기취소] 10분 내에 부스에 입장하지 않아, 대기가 취소되었어요")
    except Waiting.DoesNotExist:
        pass