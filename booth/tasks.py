from celery import shared_task
from .models import Booth

@shared_task
def reset_no_show_num():
    Booth.objects.exclude(operating_status='not_started').update(operating_status='finished')
    return "All operating_status reset to finished"