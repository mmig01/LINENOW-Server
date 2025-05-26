from celery import shared_task
from .models import CustomerUser, SMSAuthenticate

@shared_task
def reset_no_show_num():
    CustomerUser.objects.update(no_show_num=0)
    return "All no_show_num values reset to 0"

@shared_task
def reset_bad_sms_count():
    SMSAuthenticate.objects.all().update(bad_sms_count=0)
    return "All bad sms values reset to 0"