from django.urls import path, include
from .views import *

app_name = 'accounts'

urlpatterns = [
    # 일반 로그인 / 회원가입
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),    
    path('allauth/', include('allauth.urls')),

    # 회원 탈퇴
    path('accounts/withdraw/', WithdrawUserView.as_view(), name='withdraw'),
]