from django.urls import path, include
from rest_framework import routers
from .views import WaitingViewSet

app_name = "waiting"

default_router = routers.SimpleRouter(trailing_slash=False)
default_router.register('waiting', WaitingViewSet, basename='waiting')

urlpatterns = [
    path('', include(default_router.urls)),
]