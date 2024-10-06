from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Waiting
from .serializers import WaitingSerializer, WaitingDetailSerializer, WaitingCreateSerializer
from django.shortcuts import get_object_or_404
from booth.models import Booth
from accounts.models import User
from utils.exceptions import ResourceNotFound, CustomException
from utils.responses import custom_response
from django.db.models import Q
from utils.permissions import IsUser
from .tasks import check_confirmed
from utils.sendmessages import sendsms


class WaitingViewSet(viewsets.GenericViewSet):
    queryset = Waiting.objects.all()
    permission_classes = [IsUser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return WaitingSerializer
        if self.action == 'retrieve':
            return WaitingDetailSerializer
        if self.action in ['create', 'register_waiting', 'cancel_waiting', 'confirm_waiting']:
            return WaitingCreateSerializer
        return WaitingSerializer
    
    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = Waiting.objects.filter(user=user)
        serializer = self.get_serializer(queryset, many=True)
        return custom_response(data=serializer.data, message="My Waiting list fetched successfully.", code=status.HTTP_200_OK)

    def retrieve(self, request, pk=None, *args, **kwargs):
        user = request.user
        try:
            waiting = Waiting.objects.get(pk=pk, user=user)
        except Waiting.DoesNotExist:
            raise ResourceNotFound("The requested waiting information was not found.")
        serializer = self.get_serializer(waiting)
        return custom_response(data=serializer.data, message="My Waiting details fetched successfully.", code=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='register')
    def register_waiting(self, request, pk=None):
        booth = get_object_or_404(Booth, pk=pk)
        user = request.user
        
        # 부스 상태 확인
        if booth.is_operated != 'operating':
            return custom_response(data=None, message="This booth is not currently operating.", code=status.HTTP_400_BAD_REQUEST, success=False)
        
        # 사용자가 이미 해당 부스에 대기 중인 상태인지 확인
        existing_waiting = Waiting.objects.filter(
            user=user,
            booth=booth,
            waiting_status='waiting'  # waiting 상태인 경우만 체크
        ).exists()

        if existing_waiting:
            return custom_response(data=None, message="You already have a waiting for this booth. 욕심쥉이~", code=status.HTTP_400_BAD_REQUEST, success=False)
        
        # 대기가 없을 경우 새로운 대기 생성
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            if not isinstance(user, User):
                try:
                    user = User.objects.get(pk=user.pk)
                except User.DoesNotExist:
                    raise CustomException("User not found.")
            
            serializer.save(booth=booth, user=user)
            # 문자 메시지 발송
            phone_number = user.phone_number
            sendsms(phone_number, f"[라인나우] 대기가 등록되었어요 추후 입장 확정 문자를 확인해 주세요!")
            return custom_response(data=serializer.data, message="Waiting registered successfully !", code=status.HTTP_201_CREATED)
        
        return custom_response(data=serializer.errors, message="Failed to register waiting.", code=status.HTTP_400_BAD_REQUEST, success=False)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_waiting(self, request, pk=None):
        user = request.user
        waiting = get_object_or_404(Waiting, pk=pk, user=user)
        if waiting.waiting_status not in ['canceled', 'arrived']:
            waiting.set_canceled()
            return custom_response(message="Waiting canceled successfully.", code=status.HTTP_200_OK)
        return custom_response(message="This waiting has already been canceled.", code=status.HTTP_400_BAD_REQUEST, success=False)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm_waiting(self, request, pk=None):
        user = request.user
        waiting = get_object_or_404(Waiting, pk=pk, user=user)
        
        if waiting.waiting_status == 'ready_to_confirm':
            waiting.set_confirmed()       
            # 10분 후 check_confirmed task 호출
            check_confirmed.apply_async((waiting.id, waiting.user.phone_number), countdown=600)  # 10분 (600초) 후 실행

            return custom_response(message="Waiting confirmed successfully.", code=status.HTTP_200_OK)
        return custom_response(message="Unable to confirm waiting in current status.", code=status.HTTP_400_BAD_REQUEST, success=False)

    # 현재 '대기 중'인 목록만 반환하는 API
    @action(detail=False, methods=['get'], url_path='now-waitings')
    def waiting_list(self, request):
        user = request.user
        queryset = Waiting.objects.filter(user=user, waiting_status='waiting')
        serializer = self.get_serializer(queryset, many=True)
        return custom_response(data=serializer.data, message="My now waiting list fetched successfully.", code=status.HTTP_200_OK)