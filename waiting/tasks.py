from linenow.celery import app
from django.utils import timezone
import logging
from .models import Waiting
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@app.task()
def mark_waiting_as_time_over(waiting_id):
    try:
        waiting = Waiting.objects.get(waiting_id=waiting_id)
        if waiting.waiting_status == "entering":
            waiting.waiting_status = "time_over"
            customer_user = waiting.user.customer_user
            customer_user.no_show_num += 1
            customer_user.save()

            waiting.save()

            waiting_team_cnt = Waiting.objects.filter(booth=waiting.booth, waiting_status='waiting').count()
            entering_team_cnt = Waiting.objects.filter(booth=waiting.booth, waiting_status='entering').count()
            entered_team_cnt = Waiting.objects.filter(booth=waiting.booth, waiting_status='entered').count()
            canceled_team_cnt = (Waiting.objects.filter(booth=waiting.booth, waiting_status='canceled').count() + 
                                Waiting.objects.filter(booth=waiting.booth, waiting_status='time_over').count())

            try:
                channel_layer = get_channel_layer()
                admin_group_name = f"booth_{waiting.booth.booth_id}_admin"
                async_to_sync(channel_layer.group_send)(
                    admin_group_name,
                    {
                        'type': 'send_to_admin',
                        'status': 'success',
                        'message': '입장 시간이 초과되었습니다.',
                        'code': 200,
                        'data': {
                            'waiting_id': waiting.waiting_id,
                            'waiting_status': waiting.waiting_status,
                            'booth_info': {
                                'waiting_team_cnt': waiting_team_cnt,
                                'entering_team_cnt': entering_team_cnt,
                                'entered_team_cnt': entered_team_cnt,
                                'canceled_team_cnt': canceled_team_cnt
                            }
                        }
                    }
                )
            except Exception as e:
                print("WebSocket send error (cancel):", str(e))

            return waiting_id
        return None  # 상태가 entering이 아닐 경우 아무 작업 안 함
    except Waiting.DoesNotExist:
        return None  # 존재하지 않는 waiting_id 처리