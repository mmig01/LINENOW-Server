from linenow.celery import app

@app.task
def reset_no_show_num():
    from .models import CustomerUser
    CustomerUser.objects.update(no_show_num=0)
    return "All no_show_num values reset to 0"

