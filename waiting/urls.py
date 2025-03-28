from django.urls import path, include
from rest_framework import routers
from .views import WaitingViewSet, MyWaitingViewSet, MyWaitedViewSet

app_name = "waiting"

default_router = routers.SimpleRouter(trailing_slash=False)
default_router.register('waiting', WaitingViewSet, basename='waiting')

waiting_router = routers.SimpleRouter(trailing_slash=False)
waiting_router.register('waiting/my-waiting', MyWaitingViewSet, basename='my-waiting')

waited_router = routers.SimpleRouter(trailing_slash=False)
waited_router.register('waiting/my-waiting/finished', MyWaitedViewSet, basename='my-waited')

urlpatterns = [
    path('', include(default_router.urls)),
    path('', include(waiting_router.urls)),
    path('', include(waited_router.urls))
]