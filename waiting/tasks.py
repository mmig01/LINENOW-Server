from linenow.celery import app
from django.utils import timezone
import logging
from .models import Waiting

@app.task()
def mark_waiting_as_time_over(waiting_id):
    waiting = Waiting.objects.get(waiting_id=waiting_id)
    waiting.waiting_status = "time_over"
    waiting.save()
    return waiting_id
