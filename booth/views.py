from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Booth
from .serializers import BoothListSerializer, BoothDetailSerializer

class BoothViewSet(viewsets.ModelViewSet):
    queryset = Booth.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return BoothListSerializer 
        return BoothDetailSerializer 

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
