from django.urls import path, include
from rest_framework import routers

from .views import BoothViewSet, BoothWaitingStatusViewSet, BoothDataView

app_name = 'booth'

booth_router = routers.SimpleRouter(trailing_slash=False)
booth_router.register(r'booths', BoothViewSet, basename='booth')

booth_waiting_router = routers.SimpleRouter(trailing_slash=False)
booth_waiting_router.register(r'booths-waiting', BoothWaitingStatusViewSet, basename='booth-waiting')

urlpatterns = [
    path('', include(booth_router.urls)),
    path('', include(booth_waiting_router.urls)),
    path('upload-booth-data', BoothDataView.as_view(), name="upload_booth_data")
]
