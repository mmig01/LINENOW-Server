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
    # queryset = Booth.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return BoothListSerializer 
        return BoothDetailSerializer 
    
    def get_queryset(self):

        # 운영 상태에 따른 정렬 우선순위 설정 ! '운영 중 - 대기 중지 - 운영 전 - 운영종료' 순
        queryset = Booth.objects.annotate(
            # 'waiting', 'entering' 상태만 카운트
            # waiting_count=Count('waitings', filter=Q(waitings__waiting_status__in=['waiting', 'entering'])),
            operating_status_order=Case(
                When(operating_status='operating', then=Value(1)),
                When(operating_status='paused', then=Value(2)),
                When(operating_status='not_started', then=Value(3)),
                When(operating_status='finished', then=Value(4)),
                output_field=IntegerField()
            )
        )

        # 운영 상태 + 이름 순 정렬
        return queryset.order_by('operating_status_order', 'booth_name')
    
    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'], url_path='count')
    def get_booth_count(self, request):
        try:
            booth_count = Booth.objects.count()
            return custom_response({'booth_count': booth_count}, message='전체 부스 개수 조회 성공')
        except Exception as e:
            return custom_response(data=None, message='전체 부스 개수 조회 실패', code=status.HTTP_500_INTERNAL_SERVER_ERROR, success=False)
        
    def retrieve(self, request, *args, **kwargs):
        try:
            booth = self.get_object()
            serializer = self.get_serializer(booth)
            return custom_response(data=serializer.data, message="Booth detail fetched successfully", code=status.HTTP_200_OK)
        except Exception as e:
            return custom_response(data=None, message=str(e), code=status.HTTP_500_INTERNAL_SERVER_ERROR, success=False)

    @action(detail=False, methods=['get'], url_path='location')
    def get_booth_location(self, request):
        try:
            booths = Booth.objects.all()
            serializer = BoothLocationSerializer(booths, many=True)
            return custom_response(serializer.data, message='전체 부스 개수 조회 성공')
        except Exception as e:
            return custom_response(data=None, message='전체 부스 개수 조회 실패', code=status.HTTP_500_INTERNAL_SERVER_ERROR, success=False)
    
    # 에러 띄우기 위한 함수
    @action(detail=False, methods=['get'], url_path='error')
    def error(self, request):
        raise ResourceNotFound('This booth does not exist.')
    
    # 에러 띄우기 위한 함수 mk2
    @action(detail=False, methods=['get'], url_path='error2')
    def error2(self, request):
        return custom_response(data=None, message='This should not be reached', code=200, success=True)

class BoothWaitingStatusViewSet(CustomResponseMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):

    def get_serializer_class(self):
        if self.action == 'list':
            return BoothWaitingListSerializer 
        return BoothWaitingDetailSerializer 
    
    def get_queryset(self):
        # 운영 상태에 따른 정렬 우선순위 설정 ! '운영 중 - 대기 중지 - 운영 전 - 운영종료' 순
        queryset = Booth.objects.annotate(
            # 'waiting', 'entering' 상태만 카운트
            # waiting_count=Count('waitings', filter=Q(waitings__waiting_status__in=['waiting', 'entering'])),
            operating_status_order=Case(
                When(operating_status='operating', then=Value(1)),
                When(operating_status='paused', then=Value(2)),
                When(operating_status='not_started', then=Value(3)),
                When(operating_status='finished', then=Value(4)),
                output_field=IntegerField()
            )
        )
        # 운영 상태 + 이름 순 정렬
        return queryset.order_by('operating_status_order', 'booth_name')

    def retrieve(self, request, *args, **kwargs):
        try:
            booth = self.get_object()
            serializer = self.get_serializer(booth)
            return custom_response(data=serializer.data, message="Booth detail fetched successfully", code=status.HTTP_200_OK)
        except Exception as e:
            return custom_response(data=None, message=str(e), code=status.HTTP_500_INTERNAL_SERVER_ERROR, success=False)