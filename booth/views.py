from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from rest_framework.filters import OrderingFilter
from .models import Booth
from .serializers import BoothListSerializer, BoothDetailSerializer
from rest_framework import viewsets, mixins
from utils.mixins import CustomResponseMixin
from utils.responses import custom_response
from utils.exceptions import *

class BoothViewSet(CustomResponseMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    queryset = Booth.objects.all()
    filter_backends = [OrderingFilter]
    ordering_fields = ['name', 'waiting_count']
    ordering = ['name'] # 디폴트 정렬: 부스명 가나다순

    def get_serializer_class(self):
        if self.action == 'list':
            return BoothListSerializer 
        return BoothDetailSerializer 
    
    def get_queryset(self):
        queryset = Booth.objects.annotate(waiting_count=Count('waitings'))
        return queryset
    
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
            return custom_response({'booth_count': booth_count}, message='Booth count fetched successfully')
        except Exception as e:
            return custom_response(data=None, message=str(e), code=status.HTTP_500_INTERNAL_SERVER_ERROR, success=False)
    
    # 에러 띄우기 위한 함수
    @action(detail=False, methods=['get'], url_path='error')
    def error(self, request):
        raise ResourceNotFound('This booth does not exist.')
    
    # 에러 띄우기 위한 함수 mk2
    @action(detail=False, methods=['get'], url_path='error2')
    def error2(self, request):
        return custom_response(data=None, message='This should not be reached', code=200, success=True)

    # 부스별 대기 팀 수 조회 API -> 필요 없어서 주석 처리 !!
    # @action(detail=False, methods=['get'], url_path='waiting-count')
    # def booth_waiting_count(self, request):
    #     booths = Booth.objects.annotate(waiting_count=Count('waitings'))
    #     data = [
    #         {"booth_name": booth.name, "waiting_count": booth.waiting_count}
    #         for booth in booths
    #     ]
    #     return custom_response(data=data, message="Booth waiting counts fetched successfully", code=status.HTTP_200_OK)