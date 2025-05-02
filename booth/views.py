from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Case, When, Value, IntegerField, Count, Q
from rest_framework.filters import OrderingFilter
from .models import Booth
from .serializers import BoothListSerializer, BoothDetailSerializer, BoothWaitingListSerializer, BoothWaitingDetailSerializer, BoothLocationSerializer
from rest_framework import viewsets, mixins
from utils.mixins import CustomResponseMixin
from utils.responses import custom_response
from utils.exceptions import *

class BoothViewSet(CustomResponseMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    """
    - GET   /booths                 -> 부스 목록(가나다순)
    - GET   /booths/count           -> 전체 부스 개수
    - GET   /booths/location        -> 부스 위치 목록
    - GET   /booths/{pk}            -> 부스 상세
    """

    def get_serializer_class(self):
        if self.action == 'list':
            return BoothListSerializer 
        return BoothDetailSerializer 
    
    def get_queryset(self):
        # '운영중 - 대기중지 - 운영전 - 운영종료' + 가나다 순서로 정렬
        queryset = Booth.objects.annotate(
            operating_status_order=Case(
                When(operating_status='operating', then=Value(1)),
                When(operating_status='paused', then=Value(2)),
                When(operating_status='not_started', then=Value(3)),
                When(operating_status='finished', then=Value(4)),
                output_field=IntegerField()
            )
        )
        return queryset.order_by('operating_status_order', 'booth_name')

    # 부스 목록 조회
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return custom_response(
                data=serializer.data,
                message='부스 목록 조회 성공',
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)},
                message='부스 목록 조회 실패',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )

    # 전체 부스 개수 조회
    @action(detail=False, methods=['get'], url_path='count')
    def get_booth_count(self, request):
        try:
            booth_count = Booth.objects.count()
            return custom_response(
                {'booth_count': booth_count}, 
                message='전체 부스 개수 조회 성공'
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)}, 
                message='전체 부스 개수 조회 실패', 
                code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                success=False
            )

    #부스 위치 목록 조회
    @action(detail=False, methods=['get'], url_path='location')
    def get_booth_location(self, request):
        try:
            booths = Booth.objects.all()
            serializer = BoothLocationSerializer(booths, many=True)
            return custom_response(
                serializer.data, 
                message='부스 위치 목록 조회 성공',
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)}, 
                message='부스 위치 목록 조회 실패', 
                code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                success=False
            )

    #부스 상세 조회
    def retrieve(self, request, *args, **kwargs):
        try:
            booth = self.get_object()
            serializer = self.get_serializer(booth)
            return custom_response(
                data=serializer.data, 
                message="부스 상세 조회 성공", 
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)}, 
                message='부스 상세 조회 실패', 
                code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                success=False
            )

class BoothWaitingStatusViewSet(CustomResponseMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    """
    - GET   /booths-waiting         -> 부스 목록(가나다순) - 대기 정보
    - GET   /booths-waiting/{pk}    -> 부스 상세 - 대기 정보
    """

    def get_serializer_class(self):
        if self.action == 'list':
            return BoothWaitingListSerializer 
        return BoothWaitingDetailSerializer 
    
    def get_queryset(self):
        # '운영중 - 대기중지 - 운영전 - 운영종료' + 가나다 순서로 정렬
        queryset = Booth.objects.annotate(
            operating_status_order=Case(
                When(operating_status='operating', then=Value(1)),
                When(operating_status='paused', then=Value(2)),
                When(operating_status='not_started', then=Value(3)),
                When(operating_status='finished', then=Value(4)),
                output_field=IntegerField()
            )
        )
        return queryset.order_by('operating_status_order', 'booth_name')
    
    # 부스 목록 - 대기 정보 조회
    def list(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return custom_response(
                data=serializer.data,
                message='부스 대기 목록 조회 성공',
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)},
                message='부스 대기 목록 조회 실패',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )

    # 부스 상세 - 대기 정보 조회
    def retrieve(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        try:
            booth = self.get_object()
            serializer = self.get_serializer(booth)
            return custom_response(
                data=serializer.data, 
                message='부스 대기 상세 조회 성공', 
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)}, 
                message='부스 대기 상세 조회 실패', 
                code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                success=False
            )