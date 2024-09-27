from rest_framework import mixins, viewsets
from rest_framework.response import Response
from .models import *
from .serializers import *

# FAQ 리스트 조회만 가능한 ViewSet
class FAQViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer