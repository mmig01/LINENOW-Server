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
from accounts.models import CustomerUser

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .tasks import mark_waiting_as_time_over

import os, requests


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
        
        custom_user = CustomerUser.objects.filter(user=user).first()
        if not custom_user:
            return Response({
                "status": "error",
                "message": "고객 정보가 존재하지 않습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        if user.is_manager == True:
            return Response({
                "status": "error",
                "message": "관리자는 대기 신청이 불가능합니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if custom_user.no_show_num >= 3:
            return Response({
                "status": "error",
                "message": "노쇼를 3회 이상하여 대기가 불가능합니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
            sms_status = "대기 생성되었습니다."
            self.sms_sending(waiting.booth, sms_status, waiting.waiting_id)
        except Exception as e:
            print("sms send error:", str(e))
            return custom_response(
                data=None,
                message='sms 전송에 실패하였습니다.',
                code=status.HTTP_400_BAD_REQUEST
            )

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
        custom_user = CustomerUser.objects.filter(user=request.user).first()

        if not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not custom_user:
            return Response({
                "status": "error",
                "message": "고객 정보가 존재하지 않습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.is_manager == True:
            return Response({
                "status": "error",
                "message": "관리자는 대기 상세 정보 조회가 불가능합니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
    
    def sms_sending(self, booth, status, waiting_id=None):
        if status == "대기 생성되었습니다.":
            waiting = get_object_or_404(Waiting, waiting_id=waiting_id)

            if waiting:
                phone = waiting.user.user_phone.replace("-", "")
                message = f"[{booth.booth_name}] 대기 신청이 완료되었습니다. 대기 번호: {waiting.waiting_num}"

                try:
                    # 문자 발송 함수 호출 (sendsms 사용)
                    response = sendsms(phone, message)
                    # response = sms_test(phone, message)

                    if response.data['code'] == 200:
                        print(f"대기 신청 완료 문자 발송 성공: {response.data['message']}")
                    else:  # 문자 발송 실패
                        print(f"문자 발송 실패: {response.data['message']}")

                except Exception as e:
                    print(f"문자 발송 오류: {str(e)}")

        elif status == "입장 준비해주세요!":
            waiting_list = Waiting.objects.filter(
                    booth=booth,
                    waiting_status='waiting'
                ).order_by('created_at')
            
            if len(waiting_list) >= 3:
                    target_waiting = waiting_list[2]

                    if not target_waiting.notified_at:
                        phone = target_waiting.user.user_phone.replace("-", "")
                        message = f"[{booth.booth_name}] 앞에 3팀 남았습니다! 곧 입장 준비해주세요 :)"

                        # 문자 발송 함수 호출 (sendsms 사용)
                        response = sendsms(phone, message)
                        # response = sms_test(phone, message)

                        if response['code'] == 200:  # 성공적인 문자 발송
                            # 문자 발송 시간 기록
                            target_waiting.notified_at = timezone.now()
                            target_waiting.save()
                        else:  # 문자 발송 실패
                            print(f"문자 발송 실패: {response['message']}")
        
        elif status == "입장해주세요!":
            enter_waiting = get_object_or_404(Waiting, waiting_id=waiting_id)
            if enter_waiting:
                phone = enter_waiting.user.user_phone.replace("-", "")
                message = f"[{booth.booth_name}] 대기가 호출되었습니다. 10분 내에 입장해주세요!"

                try:
                    # 문자 발송 함수 호출 (sendsms 사용)
                    response = sendsms(phone, message)
                    # response = sms_test(phone, message)

                    if response['code'] == 200:  # 문자 발송 성공
                        print(f"대기 신청 완료 문자 발송 성공: {response['message']}")
                    else:  # 문자 발송 실패
                        print(f"문자 발송 실패: {response['message']}")

                except Exception as e:
                    print(f"문자 발송 오류: {str(e)}")
        
        elif status == "관리자가 대기를 취소하였습니다.":
            admin_cancel_waiting = get_object_or_404(Waiting, waiting_id=waiting_id)

            if admin_cancel_waiting:
                phone = admin_cancel_waiting.user.user_phone.replace("-", "")
                message = f"[{booth.booth_name}] 부스에서 대기를 취소하였습니다."

                try:
                    # 문자 발송 함수 호출 (sendsms 사용)
                    response = sendsms(phone, message)
                    # response = sms_test(phone, message)

                    if response['code'] == 200:  # 문자 발송 성공
                        print(f"대기 신청 완료 문자 발송 성공: {response['message']}")
                    else:  # 문자 발송 실패
                        print(f"문자 발송 실패: {response['message']}")

                except Exception as e:
                    print(f"문자 발송 오류: {str(e)}")

        else:
            print(f"적절하지 않은 상태입니다.", status)

    # 대기 취소(사용자)
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
        
        custom_user = CustomerUser.objects.filter(user=user).first()
        if not custom_user:
            return Response({
                "status": "error",
                "message": "고객 정보가 존재하지 않습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_manager == True:
            return Response({
                "status": "error",
                "message": "대기 취소에 대한 권한이 없습니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

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

        return custom_response(
            data=None,
            message="대기가 취소되었습니다.",
            code=status.HTTP_200_OK
        )
    
    # 대기 취소(관리자)
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

        if user.is_manager == False:
            return Response({
                "status": "error",
                "message": "대기 취소에 대한 권한이 없습니다.",
                "code": status.HTTP_403_FORBIDDEN,
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        waiting = get_object_or_404(Waiting, waiting_id=pk)

        waiting.waiting_status = "canceled"
        waiting.canceled_at = timezone.now()
        waiting.save()

        booth_thumbnail = BoothImage.objects.filter(booth=waiting.booth.booth_id).first()
        booth_thumbnail_url = booth_thumbnail.booth_image.url if booth_thumbnail and booth_thumbnail.booth_image else None
        
        try:
            channel_layer = get_channel_layer()
            admin_group_name = f"booth_{waiting.booth.booth_id}_admin"
            async_to_sync(channel_layer.group_send)(
                admin_group_name,
                {
                    'type': 'send_to_admin',
                    'status': 'success',
                    'message': '관리자가 대기를 취소했습니다.',
                    'code': 200,
                    'data': {
                        'waiting_id': waiting.waiting_id,
                        'waiting_status': waiting.waiting_status,
                    }
                }
            )

            user_group_name = f"user_{waiting.user.id}"
            async_to_sync(channel_layer.group_send)(
                user_group_name,
                {
                    'type': 'send_to_user',
                    'status': 'success',
                    'message': '관리자가 대기를 취소했습니다.',
                    'code': 200,
                    'data': {
                        'waiting_id': waiting.waiting_id,
                        'waiting_num': waiting.waiting_num,
                        'person_num': waiting.person_num,
                        'created_at': waiting.created_at.isoformat(),
                        'confirmed_at': waiting.confirmed_at.isoformat() if waiting.confirmed_at else None,
                        'canceled_at': waiting.canceled_at.isoformat() if waiting.canceled_at else None,
                        'waiting_status': waiting.waiting_status,
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
            print("WebSocket send error (cancel):", str(e))

        sms_status = "관리자가 대기를 취소하였습니다."
        self.sms_sending(waiting.booth, sms_status, waiting.waiting_id)

        sms_status_2 = "입장 준비해주세요."
        self.sms_sending(waiting.booth, sms_status_2)

        # serializer = WaitingDetailSerializer(waiting)
        return custom_response(
            data=None,
            message="대기가 취소되었습니다.",
            code=status.HTTP_200_OK
        )
    
    # 대기 호출
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
        
        if user.is_manager == False:
            return Response({
                "status": "error",
                "message": "대기 호출에 대한 권한이 없습니다.",
                "code": status.HTTP_403_FORBIDDEN,
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        waiting = get_object_or_404(Waiting, waiting_id=pk)

        waiting.waiting_status = "entering"
        waiting.confirmed_at = timezone.now()
        waiting.save()

        booth_thumbnail = BoothImage.objects.filter(booth=waiting.booth.booth_id).first()
        booth_thumbnail_url = booth_thumbnail.booth_image.url if booth_thumbnail and booth_thumbnail.booth_image else None

        try:
            channel_layer = get_channel_layer()

            # 관리자에게 메시지 전송
            admin_group_name = f"booth_{waiting.booth.booth_id}_admin"
            async_to_sync(channel_layer.group_send)(
                admin_group_name,
                {
                    'type': 'send_to_admin',
                    'status': 'success',
                    'message': '관리자가 대기를 호출을 성공하였습니다.',
                    'code': 200,
                    'data': {
                        'waiting_id': waiting.waiting_id,
                        'waiting_status': waiting.waiting_status,
                    }
                }
            )

            # 사용자에게 메시지 전송
            user_group_name = f"user_{waiting.user.id}"
            entering_waitings = Waiting.objects.filter(user=waiting.user, waiting_status='entering')
            entering_waitings_data = []

            for w in entering_waitings:
                booth_thumbnail = BoothImage.objects.filter(booth=w.booth.booth_id).first()
                booth_thumbnail_url = booth_thumbnail.booth_image.url if booth_thumbnail and booth_thumbnail.booth_image else None

                entering_waitings_data.append({
                    'waiting_id': w.waiting_id,
                    'waiting_num': w.waiting_num,
                    'person_num': w.person_num,
                    'created_at': w.created_at.isoformat(),
                    'confirmed_at': w.confirmed_at.isoformat() if w.confirmed_at else None,
                    'canceled_at': w.canceled_at.isoformat() if w.canceled_at else None,
                    'waiting_status': w.waiting_status,
                    'booth_info': {
                        'booth_id': w.booth.booth_id,
                        'booth_name': w.booth.booth_name,
                        'booth_location': w.booth.booth_location,
                        'booth_thumbnail': booth_thumbnail_url
                    }
                })

            # WebSocket 메시지 전송
            async_to_sync(channel_layer.group_send)(
                user_group_name,
                {
                    'type': 'send_to_user',
                    'status': 'success',
                    'message': '대기가 호출되었습니다.',
                    'code': 200,
                    'data': {
                        'entering_waitings': entering_waitings_data
                    }
                }
            )

        except Exception as e:
            print(f"WebSocket send error: {str(e)}")

        try:
            sms_status = "입장해주세요!"
            self.sms_sending(waiting.booth, sms_status, waiting.waiting_id)
        except Exception as e:
            print(f"Error 입장: {e}")

        try:
            sms_status_2 = "입장 준비해주세요!"
            self.sms_sending(waiting.booth, sms_status_2)
        except Exception as e:
            print(f"Error 입장 준비: {e}")

        try:
            mark_waiting_as_time_over.apply_async(args=[pk], countdown=600)
            print("Celery task scheduled successfully!")
        except Exception as e:
            print(f"Error scheduling task: {e}")

        # serializer = WaitingDetailSerializer(waiting)
        return custom_response(
            data=None,
            message="대기가 호출되었습니다.",
            code=status.HTTP_200_OK
        )
    
    # 대기자 도착(입장)
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm_waiting(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if user.is_manager == False:
            return Response({
                "status": "error",
                "message": "대기 도착에 대한 권한이 없습니다.",
                "code": status.HTTP_403_FORBIDDEN,
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        
        waiting = get_object_or_404(Waiting, waiting_id=pk)
        waiting.waiting_status = "entered"

        if not waiting.confirmed_at:
            return Response({
                "status": "error",
                "message": "대기 호출 시간이 존재하지 않습니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        time_diff = now - waiting.confirmed_at

        # 초 단위로 총 차이를 가져오기
        total_seconds = time_diff.total_seconds()

        # 분 단위와 초 단위 계산
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        
        # arrived_at에 "분-초" 형식으로 저장
        waiting.arrived_at = f"{minutes:02d}-{seconds:02d}"
        
        # 저장
        waiting.save()
        try:
            channel_layer = get_channel_layer()
            admin_group_name = f"booth_{waiting.booth.booth_id}_admin"
            async_to_sync(channel_layer.group_send)(
                admin_group_name,
                {
                    'type': 'send_to_admin',
                    'status': 'success',
                    'message': '입장이 완료되었습니다.',
                    'code': 200,
                    'data': {
                        'waiting_id': waiting.waiting_id,
                        'waiting_status': waiting.waiting_status,
                    }
                }
            )
        except Exception as e:
            print("WebSocket send error (cancel):", str(e))

        # serializer = WaitingDetailSerializer(waiting)
        # print(serializer.data)
        return custom_response(
            data=None,
            message="대기가 입장되었습니다.",
            code=status.HTTP_200_OK
        )

    #대기 여러개일 때 확정하기 누르면 나머지는 취소되도록
    @action(detail=True, methods=['post'], url_path='waiting-select')
    def select_waiting(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        custom_user = CustomerUser.objects.filter(user=user).first()
        if not custom_user:
            return Response({
                "status": "error",
                "message": "고객 정보가 존재하지 않습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_manager == True:
            return Response({
                "status": "error",
                "message": "대기 선택에 대한 권한이 없습니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        waiting = get_object_or_404(Waiting, waiting_id=pk)

        if waiting.waiting_status != "entering":
            return Response({
                "status": "error",
                "message": "호출된 대기만 선택할 수 있습니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cancel_waitings = Waiting.objects.filter(
            user=user,
            waiting_status="entering"
        ).exclude(waiting_id=pk)

        # 상태 업데이트
        for cancel_waiting in cancel_waitings:
            cancel_waiting.waiting_status = "canceled"
            cancel_waiting.save()

            sms_status_2 = "입장 준비해주세요."
            self.sms_sending(cancel_waiting.booth, sms_status_2)

            admin_group_name = f"booth_{cancel_waiting.booth.booth_id}_admin"
            try:
                channel_layer = get_channel_layer()
                print("channel_layer is", channel_layer)
                async_to_sync(channel_layer.group_send)(
                    admin_group_name,
                    {
                        'type': 'send_to_admin',
                        'status': 'success',
                        'message': '사용자가 대기를 취소했습니다.',
                        'code': 200,
                        'data': {
                            'waiting_id': cancel_waiting.waiting_id,
                            'waiting_status': cancel_waiting.waiting_status,
                        }
                    }
                )
            except Exception as e:
                print("WebSocket send error (cancel):", str(e))

        sms_status_2 = "입장 준비해주세요."
        self.sms_sending(waiting.booth, sms_status_2)

        serializer = WaitingListSerializer(waiting)
        return custom_response(
            data=serializer.data,
            message="대기 입장을 확정하였습니다.",
            code=status.HTTP_200_OK
        )
    
    # 입장 바텀시트 2개 이상일 때 전체 대기 취소시 필요한 정보 get
    @action(detail=False, methods=['get'], url_path='entering-waiting')
    def view_all_waiting(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        custom_user = CustomerUser.objects.filter(user=user).first()
        if not custom_user:
            return Response({
                "status": "error",
                "message": "고객 정보가 존재하지 않습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_manager == True:
            return Response({
                "status": "error",
                "message": "대기 취소에 대한 권한이 없습니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = Waiting.objects.filter(user=user, waiting_status="entering")
        entering_waitings = Waiting.objects.filter(user=user, waiting_status='entering')

        booth_names = [waiting.booth.booth_name for waiting in entering_waitings]
        booth_count = entering_waitings.count()

        if not queryset.exists():
            return Response({
                "status": "error",
                "message": "입장중인 내역이 없습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "status": "success",
            "message": "입장중인 나의 대기 리스트 가져오기 성공!",
            "code": status.HTTP_200_OK,
            "data": {
                "booth_names": booth_names,
                "count": booth_count
            }
        })

    # 입장 차례 대기 전체 취소
    @action(detail=False, methods=['post'], url_path='cancel-all-entering-waiting')
    def cancel_all_entering_waiting(self, request):
        user = request.user
        
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        custom_user = CustomerUser.objects.filter(user=user).first()
        if not custom_user:
            return Response({
                "status": "error",
                "message": "고객 정보가 존재하지 않습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_manager == True:
            return Response({
                "status": "error",
                "message": "대기 취소에 대한 권한이 없습니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        waitings = Waiting.objects.filter(
            user=user,
            waiting_status="entering"
        )

        if not waitings.exists():
            return Response({
                "status": "error",
                "message": "호출된 대기가 없습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        for cancel_waiting in waitings:
            cancel_waiting.waiting_status = "canceled"
            cancel_waiting.save()

            sms_status_2 = "입장 준비해주세요."
            self.sms_sending(cancel_waiting.booth, sms_status_2)

            admin_group_name = f"booth_{cancel_waiting.booth.booth_id}_admin"
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    admin_group_name,
                    {
                        'type': 'send_to_admin',
                        'status': 'success',
                        'message': '사용자가 대기를 취소하였습니다.',
                        'code': 200,
                        'data': {
                            'waiting_id': cancel_waiting.waiting_id,
                            'waiting_status': cancel_waiting.waiting_status,
                        }
                    }
                )
            except Exception as e:
                print("WebSocket send error (cancel):", str(e))

        return custom_response(
            data=None,
            message="입장이 취소되었습니다.",
            code=status.HTTP_200_OK
        )

    # 입장 바텀시트 1개일 때 전체 대기 취소 시 필요한 정보 get
    @action(detail=False, methods=['get'], url_path='view-waiting')
    def view_waiting(self,request):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        custom_user = CustomerUser.objects.filter(user=user).first()
        if not custom_user:
            return Response({
                "status": "error",
                "message": "고객 정보가 존재하지 않습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_manager == True:
            return Response({
                "status": "error",
                "message": "해당 요청에 대한 권한이 없습니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = Waiting.objects.filter(user=user, waiting_status="waiting")
        entering_waitings = Waiting.objects.filter(user=user, waiting_status='waiting')

        booth_names = [waiting.booth.booth_name for waiting in entering_waitings]
        booth_count = entering_waitings.count()

        if not queryset.exists():
            return Response({
                "status": "error",
                "message": "대기중인 내역이 없습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "status": "success",
            "message": "대기중인 나의 대기 리스트 가져오기 성공!",
            "code": status.HTTP_200_OK,
            "data": {
                "booth_names": booth_names,
                "count": booth_count
            }
        })

    # 호출 왔을 때 대기중인 모든 대기 취소
    @action(detail=False, methods=['post'], url_path='cancel-all-waiting')
    def cancel_all_waiting(self, request):
        user = request.user

        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        custom_user = CustomerUser.objects.filter(user=user).first()
        if not custom_user:
            return Response({
                "status": "error",
                "message": "고객 정보가 존재하지 않습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_manager == True:
            return Response({
                "status": "error",
                "message": "대기 취소에 대한 권한이 없습니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        entering_waiting = Waiting.objects.filter(user=user, waiting_status="entering")

        if not entering_waiting.exists():
            return Response({
                "status": "error",
                "message": "호출된 대기가 없습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)


        waitings = Waiting.objects.filter(
            user=user,
            waiting_status="waiting"
        )

        for cancel_waiting in waitings:
            cancel_waiting.waiting_status = "canceled"
            cancel_waiting.save()

            sms_status_2 = "입장 준비해주세요."
            self.sms_sending(cancel_waiting.booth, sms_status_2)

            admin_group_name = f"booth_{cancel_waiting.booth.booth_id}_admin"
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    admin_group_name,
                    {
                        'type': 'send_to_admin',
                        'status': 'success',
                        'message': '사용자가 대기를 취소하였습니다.',
                        'code': 200,
                        'data': {
                            'waiting_id': cancel_waiting.waiting_id,
                            'waiting_status': cancel_waiting.waiting_status,
                        }
                    }
                )
            except Exception as e:
                print("WebSocket send error (cancel):", str(e))

        return custom_response(
            data=None,
            message="대기가 취소되었습니다.",
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
        
        custom_user = CustomerUser.objects.filter(user=user).first()
        if not custom_user:
            return Response({
                "status": "error",
                "message": "고객 정보가 존재하지 않습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_manager == True:
            return Response({
                "status": "error",
                "message": "해당 요청에 대한 권한이 없습니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 대기 중인 내역 가져오기
        queryset = Waiting.objects.filter(user=user, waiting_status__in=["waiting", "entering"])
        serializer = WaitingListSerializer(queryset, many=True)

        if not queryset.exists():
            return Response({
                "status": "error",
                "message": "입장 호출된 내역이 없습니다.",
                "code": status.HTTP_200_OK,
                "data": None
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "success",
            "message": "입장 리스트 가져오기 성공!",
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
        
        custom_user = CustomerUser.objects.filter(user=user).first()
        if not custom_user:
            return Response({
                "status": "error",
                "message": "고객 정보가 존재하지 않습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_manager == True:
            return Response({
                "status": "error",
                "message": "해당 요청에 대한 권한이 없습니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        waiting_count = Waiting.objects.filter(user=user, waiting_status__in=["waiting", "entering"]).count()
        waiting_finished_count = Waiting.objects.filter(user=user).exclude(waiting_status__in=["waiting", "entering"]).count()

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
        
        custom_user = CustomerUser.objects.filter(user=user).first()
        if not custom_user:
            return Response({
                "status": "error",
                "message": "고객 정보가 존재하지 않습니다.",
                "code": status.HTTP_404_NOT_FOUND,
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_manager == True:
            return Response({
                "status": "error",
                "message": "해당 요청에 대한 권한이 없습니다.",
                "code": status.HTTP_400_BAD_REQUEST,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 종료된 대기 내역 가져오기
        queryset = Waiting.objects.filter(user=user).exclude(waiting_status__in=["waiting", "entering"])
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