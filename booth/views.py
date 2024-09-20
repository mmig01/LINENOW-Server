from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from rest_framework.filters import OrderingFilter
from .models import Booth
from .serializers import BoothListSerializer, BoothDetailSerializer

class BoothViewSet(viewsets.ModelViewSet):
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
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='count')
    def get_booth_count(self, request):
        booth_count = Booth.objects.count()
        return Response({'booth_count': booth_count}, status=status.HTTP_200_OK)