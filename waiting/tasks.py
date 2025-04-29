from linenow.celery import app
from django.utils import timezone
import logging
from .models import Waiting

@app.task()
def mark_waiting_as_time_over(waiting_id):
    try:
        waiting = Waiting.objects.get(waiting_id=waiting_id)
        if waiting.waiting_status == "entering":
            waiting.waiting_status = "time_over"
            waiting.save()
            return waiting_id
        return None  # 상태가 entering이 아닐 경우 아무 작업 안 함
    except Waiting.DoesNotExist:
        return None  # 존재하지 않는 waiting_id 처리