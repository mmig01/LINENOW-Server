from django.contrib import admin
from django.urls import path, include
from .views import *

app_name = 'accounts'

urlpatterns = [
    path('allauth/', include('allauth.urls')),

    # 카카오 로그인
    path('accounts/kakao/callback/', kakao_callback, name='kakao_callback'),
    path('accounts/kakao/login/finish/', KakaoLogin.as_view(), name='kakao_login_todjango'),
]