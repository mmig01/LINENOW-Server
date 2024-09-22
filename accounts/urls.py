from django.contrib import admin
from django.urls import path, include
from .views import kakao_callback, KakaoLogin

app_name = 'accounts'

urlpatterns = [
    # 회원가입 및 로그인
    path('accounts/', include('dj_rest_auth.urls')),
    path('accounts/registration/', include('dj_rest_auth.registration.urls')),
    path('accounts/', include('allauth.urls')),

    # 카카오 API
    path('accounts/kakao/callback/', kakao_callback, name='kakao_callback'),
    path('accounts/kakao/login/finish/', KakaoLogin.as_view(), name='kakao_login_todjango'),
]