from linenow.celery import app
from django.utils import timezone
import logging
from .models import Waiting
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from utils.sendmessages import sendsms

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

            if waiting:
                phone = waiting.user.user_phone.replace("-", "")
                message = "[대기취소]\n입장 차례인 부스에 입장하시지 않아, 대기가 취소되었어요"
                
                try:
                    response = sendsms(phone, message)

                    if response.data['code'] == 200:
                        print(f"입장 시간 초과 문자 발송 성공: {response.data['message']}")
                    else:  # 문자 발송 실패
                        print(f"문자 발송 실패: {response.data['message']}")

                except Exception as e:
                    print(f"문자 발송 오류: {str(e)}")

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

            user = waiting.user
            time_over_user_waitings = Waiting.objects.filter(
                user=user,
                waiting_status__in=["waiting", "entering"]
            )
            for time_over_user_waiting in time_over_user_waitings:
                waiting_status_check = time_over_user_waiting.waiting_status
                time_over_user_waiting.waiting_status = "canceled"
                time_over_user_waiting.save()

                waiting_team_cnt_1 = Waiting.objects.filter(booth=time_over_user_waiting.booth, waiting_status='waiting').count()
                entering_team_cnt_1 = Waiting.objects.filter(booth=time_over_user_waiting.booth, waiting_status='entering').count()
                entered_team_cnt_1 = Waiting.objects.filter(booth=time_over_user_waiting.booth, waiting_status='entered').count()
                canceled_team_cnt_1 = (Waiting.objects.filter(booth=time_over_user_waiting.booth, waiting_status='canceled').count() + 
                                    Waiting.objects.filter(booth=time_over_user_waiting.booth, waiting_status='time_over').count())
                
                admin_group_name = f"booth_{time_over_user_waiting.booth.booth_id}_admin"
                try:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        admin_group_name,
                        {
                            'type': 'send_to_admin',
                            'status': 'success',
                            'message': '사용자가 대기를 취소했습니다.',
                            'code': 200,
                            'data': {
                                'waiting_id': time_over_user_waiting.waiting_id,
                                'waiting_status': time_over_user_waiting.waiting_status,
                                'booth_info': {
                                    'waiting_team_cnt': waiting_team_cnt_1,
                                    'entering_team_cnt': entering_team_cnt_1,
                                    'entered_team_cnt': entered_team_cnt_1,
                                    'canceled_team_cnt': canceled_team_cnt_1
                                }
                            }
                        }
                    )
                except Exception as e:
                    print("WebSocket send error (cancel):", str(e))

                if waiting_status_check == "waiting":
                    waiting_list = Waiting.objects.filter(
                        booth=time_over_user_waiting.booth,
                        waiting_status='waiting'
                    ).order_by('created_at')

                    if len(waiting_list) >= 3:
                        target_waiting = waiting_list[2]

                        if not target_waiting.notified_at:
                            phone = target_waiting.user.user_phone.replace("-", "")
                            message = "[라인나우]\n내 앞으로 3팀이 남았어요\n입장 순서가 다가오니 준비해주세요"

                            # 문자 발송 함수 호출 (sendsms 사용)
                            response = sendsms(phone, message)

                            if response.data['code'] == 200:  # 성공적인 문자 발송
                                target_waiting.notified_at = timezone.now()
                                target_waiting.save()
                            else:  # 문자 발송 실패
                                print(f"문자 발송 실패2: {response.data['message']}")

            return waiting_id
        return None  # 상태가 entering이 아닐 경우 아무 작업 안 함
    except Waiting.DoesNotExist:
        return None  # 존재하지 않는 waiting_id 처리