# myapp/urls.py
from django.db import router
from django.urls import path, include
from rest_framework import routers
from .views import UserViewSet, SMSViewSet
app_name = 'accounts'
accounts_router = routers.SimpleRouter(trailing_slash=False)
accounts_router.register('accounts', UserViewSet, basename='accounts')

sms_router = routers.SimpleRouter(trailing_slash=False)
sms_router.register('', SMSViewSet, basename='sms-auth')
urlpatterns = [
    path('', include(accounts_router.urls)),
    path('accounts/registration/', include(sms_router.urls)),
]