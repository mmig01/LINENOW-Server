import os
from celery import Celery
from django.conf import settings
# Django 프로젝트 설정 불러오기
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linenow.settings')

app = Celery('linenow')

# Django 설정에서 Celery 관련 설정 불러오기
app.config_from_object('django.conf:settings', namespace='CELERY')

# 프로젝트 내 모든 등록된 앱에서 task를 자동으로 찾아 등록
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))