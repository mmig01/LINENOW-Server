from collections import defaultdict
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

from .models import Waiting
from booth.models import Booth, BoothImage

User = get_user_model()

class WaitingConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope["user"]

            self.booth_id = self.scope['url_route']['kwargs']['booth_id']
            query_params = parse_qs(self.scope["query_string"].decode("utf-8"))
            self.user_type = query_params.get("user_type", ["user"])[0]  # "admin" or "user"

            print("user_type:", self.user_type)

            self.admin_group_name = f"booth_{self.booth_id}_admin"
            self.user_group_name = f"booth_{self.booth_id}_users"

            if self.user.is_authenticated:
                if self.user_type == "admin":
                    await self.channel_layer.group_add(self.admin_group_name, self.channel_name)
                else:
                    await self.channel_layer.group_add(self.user_group_name, self.channel_name)

                await self.accept()
            else:
                await self.close()
        
        except Exception as e:
            await self.send_json({'error': f'연결 오류: {str(e)}'})

    async def disconnect(self, close_code):
        try:
            if self.user_type == "admin":
                await self.channel_layer.group_discard(self.admin_group_name, self.channel_name)
            else:
                await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

            print(f"[DISCONNECT] booth_id={self.booth_id}, user_type={self.user_type}, close_code={close_code}")
        except Exception as e:
            print(f"[DISCONNECT ERROR] {str(e)}")
    
    async def receive_json(self, content):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.send_json({
                'type': 'error',
                'message': '인증된 사용자만 이용할 수 있습니다.',
                'data': ''
            })
            await self.close()
            return
        
        request_user = content.get('user_id')
        waiting_action = content.get('waiting_action')
        waiting_info = await self.get_user_waiting_info(request_user, self.booth_id)
        booth_info = await self.get_booth_info(self.booth_id)
        booth_thumbnail = await self.get_booth_thumbnail(self.booth_id)

        booth_thumbnail_url = None
        if booth_thumbnail and booth_thumbnail.image:
            booth_thumbnail_url = booth_thumbnail.image.url 

        waiting_cnt = await self.get_waiting_cnt(self.booth_id)
        entering_cnt = await self.get_entering_cnt(self.booth_id)
        entered_cnt = await self.get_entered_cnt(self.booth_id)
        canceled_cnt =await self.get_canceled_cnt(self.booth_id)

        # 사용자가 대기 신청
        if waiting_action == "waiting_request":
            await self.channel_layer.group_send(
                self.admin_group_name,
                {
                    'type': 'send_to_admin',
                    'status': 'success',
                    'message': '사용자가 새로운 대기를 등록하였습니다.',
                    'code': 200,
                    'data': {
                        'action': 'create',
                        'waiting_id': waiting_info.waiting_id,
                        'waiting_num': waiting_info.waiting_num,
                        'person_num': waiting_info.person_num,
                        'waiting_status': waiting_info.waiting_status,
                        'created_at': waiting_info.created_at,
                        'confirmed_at': waiting_info.confirmed_at,
                        'canceled_at': waiting_info.canceled_at,
                        'user_info': {
                            'user_name': request_user.user_name,
                            'user_phone': request_user.user_phone
                        },
                        'waiting_cnt': waiting_cnt,
                        'entering_cnt': entering_cnt,
                        'entered_cnt': entered_cnt,
                        'canceled_cnt': canceled_cnt
                    }
                }
            )

        # 사용자가 대기 취소 (사용자 -> 관리자)
        elif waiting_action == "waiting_cancel_by_user":
            await self.channel_layer.group_send(
                self.admin_group_name,
                {
                    'type': 'send_to_admin',
                    'status': 'success',
                    'message': '사용자가 대기를 취소하였습니다.',
                    'code': 200,
                    'data': {
                        'action': 'update',
                        'waiting_id': waiting_info.waiting_id,
                        'waiting_status': waiting_info.waiting_status,
                        'canceled_at': waiting_info.canceled_at,
                        'waiting_cnt': waiting_cnt,
                        'entering_cnt': entering_cnt,
                        'entered_cnt': entered_cnt,
                        'canceled_cnt': canceled_cnt
                    }
                }
            )
        
        # 관리자가 대기 호출 (관리자 -> 사용자)
        elif waiting_action == "waiting_call":
            waiting_num = content.get('waiting_num')
            called_waiting_info = await self.get_waiting_info(self.booth_id, waiting_num)
            await self.channel_layer.group_send(
                self.user_group_name,
                {
                    'type': 'send_to_user',
                    'status': 'success',
                    'message': '관리자가 대기를 호출하였습니다.',
                    'code': 200,
                    'data': {
                        'action': 'update',
                        'waiting_id': called_waiting_info.waiting_id,
                        'waiting_num': called_waiting_info.waiting_num,
                        'waiting_status': 'entering',
                        'booth_info': {
                            'booth_id': self.booth_id,
                            'booth_name': booth_info.booth_name,
                            'booth_thumbnail': booth_thumbnail_url,
                            'booth_location': booth_info.booth_location
                        },
                        'person_num': called_waiting_info.person_num,
                    }
                }
            )

        
        elif waiting_action == "time_over":
            waiting_num = content.get('waiting_num')
            time_over_waiting_info = await self.get_waiting_info(self.booth_id, waiting_num)
            await self.channel_layer.group_send(
                self.admin_group_name,
                {
                    'type': 'send_to_admin',
                    'status': 'success',
                    'message': '시간 초과로 인해 대기가 취소되었습니다.',
                    'code': 200,
                    'data': {
                        'action': 'update',
                        'waiting_id': time_over_waiting_info.waiting_id,
                        'waiting_num': time_over_waiting_info.waiting_num,
                        'waiting_status': 'time_over',
                        'waiting_cnt': waiting_cnt,
                        'entering_cnt': entering_cnt,
                        'entered_cnt': entered_cnt,
                        'canceled_cnt': canceled_cnt
                    }
                }
            )
        
        else:
            await self.send_json(
                {
                    'type': 'error',
                    'status': 'fail',
                    'message': '올바르지 않은 요청입니다.',
                    'code': 400,
                    'data': {}
                }
            )
            await self.close()
    
    async def send_to_admin(self, event):
        await self.send_json({
            'status': event.get('status'),
            'message': event.get('message'),
            'code': event.get('code'),
            'data': event.get('data'),
        })
    
    async def send_to_user(self, event):
        await self.send_json({
            'status': event.get('status'),
            'message': event.get('message'),
            'code': event.get('code'),
            'data': event.get('data'),
        })

    @database_sync_to_async
    def get_user_waiting_info(self, request_user, booth_id):
        try:
            return Waiting.objects.get(user=request_user, booth=booth_id)
        except Waiting.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_waiting_cnt(self, booth_id):
        return Waiting.objects.filter(booth=booth_id, waiting_status="waiting").count()
    
    @database_sync_to_async
    def get_entering_cnt(self, booth_id):
        return Waiting.objects.filter(booth=booth_id, waiting_status="entering").count()
    
    @database_sync_to_async
    def get_entered_cnt(self, booth_id):
        return Waiting.objects.filter(booth=booth_id, waiting_status="entered").count()
    
    @database_sync_to_async
    def get_canceled_cnt(self, booth_id):
        canceled_cnt = Waiting.objects.filter(booth=booth_id, waiting_status="canceled").count()
        time_over_cnt = Waiting.objects.filter(booth=booth_id, waiting_status="time_over").count()
        return canceled_cnt + time_over_cnt
    
    @database_sync_to_async
    def get_waiting_info(self, booth_id, waiting_num):
        return Waiting.objects.get(booth=booth_id, waiting_num=waiting_num)

    @database_sync_to_async
    def get_booth_info(self, booth_id):
        return Booth.objects.filter(booth_id=booth_id)
    
    @database_sync_to_async
    def get_booth_thumbnail(self, booth_id):
        return BoothImage.objects.filter(booth=booth_id).first()