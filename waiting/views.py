from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Waiting
from .serializers import WaitingSerializer, WaitingDetailSerializer, WaitingCreateSerializer
from django.shortcuts import get_object_or_404
from booth.models import Booth
from django.contrib.auth.models import User
from utils.mixins import CustomResponseMixin
from utils.exceptions import ResourceNotFound, CustomException
from utils.responses import custom_response


class WaitingViewSet(viewsets.GenericViewSet):
    queryset = Waiting.objects.all()
    
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
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = request.user
            if not isinstance(user, User):
                try:
                    user = User.objects.get(pk=user.pk)
                except User.DoesNotExist:
                    raise CustomException("User not found.")
            
            serializer.save(booth=booth, user=user)
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
            return custom_response(message="Waiting confirmed successfully.", code=status.HTTP_200_OK)
        return custom_response(message="Unable to confirm waiting in current status.", code=status.HTTP_400_BAD_REQUEST, success=False)

    # 현재 '대기 중'인 목록만 반환하는 API
    @action(detail=False, methods=['get'], url_path='now-waiting')
    def waiting_list(self, request):
        user = request.user
        queryset = Waiting.objects.filter(user=user, waiting_status='waiting')
        serializer = self.get_serializer(queryset, many=True)
        return custom_response(data=serializer.data, message="My now waiting list fetched successfully.", code=status.HTTP_200_OK)