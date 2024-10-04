from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

app_name = 'sms'

router = DefaultRouter()
router.register(r'sendsms', sendsms, basename='sendsms')

urlpatterns = [
    path('sms/sendsms', sendsms, name='sendsms')
]