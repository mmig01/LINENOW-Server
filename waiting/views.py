from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Waiting
from .serializers import WaitingSerializer, WaitingDetailSerializer, WaitingCreateSerializer
from django.shortcuts import get_object_or_404
from booth.models import Booth
from django.contrib.auth.models import User


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
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None, *args, **kwargs):
        user = request.user
        waiting = get_object_or_404(Waiting, pk=pk, user=user)
        serializer = self.get_serializer(waiting)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
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
                    return Response({'error': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save(booth=booth, user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_waiting(self, request, pk=None):
        user = request.user
        waiting = get_object_or_404(Waiting, pk=pk, user=user)
        if waiting.waiting_status not in ['canceled', 'arrived']:
            waiting.set_canceled()
            return Response({'status': '대기 취소 완료'}, status=status.HTTP_200_OK)
        return Response({'status': '이미 취소된 대기입니다.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm_waiting(self, request, pk=None):
        user = request.user
        waiting = get_object_or_404(Waiting, pk=pk, user=user)
        if waiting.waiting_status == 'ready_to_confirm':
            waiting.set_confirmed()
            return Response({'status': '입장 확정 완료'}, status=status.HTTP_200_OK)
        return Response({'status': '확정할 수 없는 상태입니다.'}, status=status.HTTP_400_BAD_REQUEST)
