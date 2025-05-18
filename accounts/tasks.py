from celery import shared_task
from .models import CustomerUser

@shared_task
def reset_no_show_num():
    CustomerUser.objects.update(no_show_num=0)
    return "All no_show_num values reset to 0"
