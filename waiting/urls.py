from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WaitingViewSet

router = DefaultRouter()
router.register(r'waitings', WaitingViewSet, basename='waiting')

urlpatterns = [
    path('', include(router.urls)),
]