from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Django 프로젝트 설정 불러오기
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linenow.settings')

app = Celery('linenow')

# Django 설정에서 Celery 관련 설정 불러오기
app.config_from_object('django.conf:settings', namespace='CELERY')

# 프로젝트 내 모든 등록된 앱에서 task를 자동으로 찾아 등록
app.autodiscover_tasks()

# 셀러리 테스트용 디버그 작업 - 제대로 작동하는지 확인하기 위해 간단한 디버그 작업 추가 !!
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
