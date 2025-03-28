from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Waiting
from .serializers import WaitingListSerializer, WaitingDetailSerializer
from django.shortcuts import get_object_or_404
from booth.models import Booth
from accounts.models import User
from utils.exceptions import ResourceNotFound, CustomException
from utils.responses import custom_response
from django.db.models import Q
from utils.permissions import IsUser
from .tasks import check_confirmed
from utils.sendmessages import sendsms
from django.utils import timezone

# 편의를 위해서 http에서 대기 생성할 수 있도록 한 것(모든 대기)
class WaitingViewSet(viewsets.ModelViewSet):
    queryset = Waiting.objects.all()
    
    def get_serializer_class(self):
        if self.action == "list":
            return WaitingListSerializer
        return WaitingDetailSerializer

# 나의 대기
class MyWaitingViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Waiting.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return WaitingListSerializer
        return WaitingDetailSerializer
    
    def list(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        queryset = Waiting.objects.filter(user=user, waiting_status="waiting")
        serializer = self.get_serializer(queryset, many=True)
        return custom_response(data=serializer.data, message="대기중인 나의 대기 리스트 가져오기 성공!", code=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        queryset = Waiting.objects.filter(user=user, waiting_status="waiting")
        serializer = self.get_serializer(queryset, many=True)
        return custom_response(data=serializer.data, message="대기중인 대기 상세 가져오기 성공!", code=status.HTTP_200_OK)
    
class MyWaitedViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = WaitingListSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Waiting.objects.none()  # 로그인하지 않은 경우 빈 QuerySet 반환
        
        return Waiting.objects.filter(user=user).exclude(waiting_status__in=["waiting", "not_waiting"])

    def list(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return custom_response(
            data=serializer.data,
            message="종료된 대기 리스트 가져오기 성공!",
            code=status.HTTP_200_OK
        )