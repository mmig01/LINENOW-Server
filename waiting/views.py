from venv import logger
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Waiting
from .serializers import WaitingListSerializer, WaitingDetailSerializer
from django.shortcuts import get_object_or_404
from booth.models import Booth, BoothImage
from accounts.models import User
from utils.exceptions import ResourceNotFound, CustomException
from utils.responses import custom_response
from django.db.models import Q
from utils.sendmessages import sendsms
from django.utils import timezone
from manager.models import Manager

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .tasks import mark_waiting_as_time_over

def send_websocket_message(waiting, booth_thumbnail_url, status_message, user_message):
    try:
        channel_layer = get_channel_layer()

        # 관리자에게 메시지 전송
        admin_group_name = f"booth_{waiting.booth.booth_id}_admin"
        async_to_sync(channel_layer.group_send)(
            admin_group_name,
            {
                'type': 'send_to_admin',
                'status': 'success',
                'message': status_message,
                'code': 200,
                'data': {
                    'waiting_id': waiting.waiting_id,
                    'waiting_status': waiting.waiting_status,
                }
            }
        )

        # 사용자에게 메시지 전송
        user_group_name = f"user_{waiting.user.id}"
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'send_to_user',
                'status': 'success',
                'message': user_message,
                'code': 200,
                'data': {
                    'waiting_id': waiting.waiting_id,
                    'waiting_num': waiting.waiting_num,
                    'person_num': waiting.person_num,
                    'created_at': waiting.created_at.isoformat(),
                    'confirmed_at': waiting.confirmed_at.isoformat() if waiting.confirmed_at else None,
                    'canceled_at': waiting.canceled_at.isoformat() if waiting.canceled_at else None,
                    'booth_info': {
                        'booth_id': waiting.booth.booth_id,
                        'booth_name': waiting.booth.booth_name,
                        'booth_location': waiting.booth.booth_location,
                        'booth_thumbnail': booth_thumbnail_url
                    }
                }
            }
        )

    except Exception as e:
        print(f"WebSocket send error: {str(e)}")

# 편의를 위해서 http에서 대기 생성할 수 있도록 한 것(모든 대기)
class WaitingViewSet(viewsets.ModelViewSet):
    queryset = Waiting.objects.all()
    
    def get_serializer_class(self):
        if self.action == "list":
            return WaitingListSerializer
        return WaitingDetailSerializer
    
    def create(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        booth_id = request.data.get('booth_id')
        person_num = request.data.get('person_num')

        if not booth_id:
            return Response({
                "status": "error",
                "message": "부스 ID가 필요합니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        booth = get_object_or_404(Booth, booth_id=booth_id)
        waiting_num = booth.current_watiting_num + 1

        # 중복 대기 방지 (선택)
        existing_waiting = Waiting.objects.filter(user=user, booth=booth, waiting_status="waiting").first()
        if existing_waiting:
            return Response({
                "status": "error",
                "message": "이미 대기 중입니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        # 대기 생성
        waiting = Waiting.objects.create(
            user=user,
            booth=booth,
            person_num=person_num,
            waiting_num = waiting_num,
            waiting_status="waiting",
        )

        booth.current_watiting_num = waiting_num
        booth.save()

        try:
            channel_layer = get_channel_layer()
            admin_group_name = f"booth_{booth.booth_id}_admin"
            async_to_sync(channel_layer.group_send)(
                admin_group_name,
                {
                    'type': 'send_to_admin',  # consumer 쪽의 handler 함수 이름 (ex: def send_to_admin(self, event))
                    'status': 'success',
                    'message': '사용자가 새로운 대기를 등록했습니다.',
                    'code': 200,
                    'data': {
                        'action': 'create',
                        'waiting_id': waiting.waiting_id,
                        'waiting_num': waiting.waiting_num,
                        'person_num': waiting.person_num,
                        'waiting_status': waiting.waiting_status,
                        'created_at': waiting.created_at.isoformat(),
                        'confirmed_at': waiting.confirmed_at.isoformat() if waiting.confirmed_at else None,
                        'canceled_at': waiting.canceled_at.isoformat() if waiting.canceled_at else None,
                        'user_info': {
                            'user_name': user.user_name,  # request.user 기준
                            'user_phone': user.user_phone,  # 필요에 따라 수정
                        }
                    }
                }
            )
        except Exception as e:
            print("WebSocket send error:", str(e))

        try:
            serializer = WaitingDetailSerializer(waiting)  
        
        except Exception as e:
            raise e
        return custom_response(
            data=serializer.data,
            message="대기 신청이 완료되었습니다!",
            code=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({
                "status": "error",
                "message": "본인의 대기만 조회할 수 있습니다.",
                "code": status.HTTP_403_FORBIDDEN,
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance)
        return custom_response(
            data=serializer.data,
            message="대기 상세 정보 가져오기 성공!",
            code=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='user-cancel')
    def user_cancel_waiting(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)

        waiting = get_object_or_404(Waiting, waiting_id=pk)

        if waiting.user != user:
            return Response({
                "status": "error",
                "message": "본인의 대기만 취소할 수 있습니다.",
                "code": status.HTTP_403_FORBIDDEN,
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        waiting.waiting_status = "canceled"
        waiting.canceled_at = timezone.now()
        waiting.save()

        # WebSocket 메시지 전송
        try:
            channel_layer = get_channel_layer()
            admin_group_name = f"booth_{waiting.booth.booth_id}_admin"
            async_to_sync(channel_layer.group_send)(
                admin_group_name,
                {
                    'type': 'send_to_admin',
                    'status': 'success',
                    'message': '사용자가 대기를 취소했습니다.',
                    'code': 200,
                    'data': {
                        'waiting_id': waiting.waiting_id,
                        'waiting_status': waiting.waiting_status,
                    }
                }
            )
        except Exception as e:
            print("WebSocket send error (cancel):", str(e))

        serializer = WaitingDetailSerializer(waiting)
        return custom_response(
            data=serializer.data,
            message="대기가 취소되었습니다.",
            code=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='manager-cancel')
    def manager_cancel_waiting(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)

        waiting = get_object_or_404(Waiting, waiting_id=pk)

        waiting.waiting_status = "canceled"
        waiting.canceled_at = timezone.now()
        waiting.save()

        booth_thumbnail = BoothImage.objects.filter(booth=waiting.booth.booth_id).first()
        booth_thumbnail_url = booth_thumbnail.booth_image.url if booth_thumbnail and booth_thumbnail.booth_image else None
        send_websocket_message(waiting, booth_thumbnail_url, '관리자가 대기를 취소했습니다.', '대기가 취소되었습니다.')

        serializer = WaitingDetailSerializer(waiting)
        return custom_response(
            data=serializer.data,
            message="대기가 취소되었습니다.",
            code=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='call')
    def call_waiting(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)

        waiting = get_object_or_404(Waiting, waiting_id=pk)

        waiting.waiting_status = "entering"
        waiting.confirmed_at = timezone.now()
        waiting.save()

        booth_thumbnail = BoothImage.objects.filter(booth=waiting.booth.booth_id).first()
        booth_thumbnail_url = booth_thumbnail.booth_image.url if booth_thumbnail and booth_thumbnail.booth_image else None
        send_websocket_message(waiting, booth_thumbnail_url, '관리자가 대기를 호출했습니다.', '대기가 호출되었습니다.')
        print("[DEBUG] Scheduling mark_waiting_as_time_over with id:", pk)
        print("Scheduling Celery task...")
        try:
            mark_waiting_as_time_over.apply_async(args=[pk], countdown=30)
            print("Celery task scheduled successfully!")
        except Exception as e:
            print(f"Error scheduling task: {e}")

        serializer = WaitingDetailSerializer(waiting)
        return custom_response(
            data=serializer.data,
            message="대기가 호출되었습니다.",
            code=status.HTTP_200_OK
        )
    @action(detail=False, methods=['get'], url_path='my-waiting')
    def my_waiting(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 대기 중인 내역 가져오기
        queryset = Waiting.objects.filter(user=user, waiting_status="waiting")
        serializer = WaitingListSerializer(queryset, many=True)

        if not queryset.exists():
            return Response({
                "status": "error",
                "message": "대기 중인 내역이 없습니다.",
                "code": status.HTTP_200_OK,
                "data": None
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "success",
            "message": "대기중인 나의 대기 리스트 가져오기 성공!",
            "code": status.HTTP_200_OK,
            "data": serializer.data
        })

    @action(detail=False, methods=['get'], url_path='my-waiting/count')
    def my_waiting_count(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        waiting_count = Waiting.objects.filter(user=user, waiting_status="waiting").count()
        waiting_finished_count = Waiting.objects.filter(user=user).exclude(waiting_status="waiting").count()

        return Response({
            "status": "success",
            "message": "대기 중인 나의 대기 수 가져오기 성공!",
            "code": status.HTTP_200_OK,
            "data": {
                "waiting_count": waiting_count,
                "waiting_finished_count": waiting_finished_count
            }
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='my-waited')
    def my_waited(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 종료된 대기 내역 가져오기
        queryset = Waiting.objects.filter(user=user).exclude(waiting_status="waiting")
        serializer = WaitingListSerializer(queryset, many=True)
        
        data = []
        for item in serializer.data:
            filtered_item = {key: value for key, value in item.items() if key != 'waiting_team_ahead'}
            data.append(filtered_item)

        return Response({
            "status": "success",
            "message": "대기 종료된 나의 대기 리스트 가져오기 성공!",
            "code": status.HTTP_200_OK,
            "data": data
        })