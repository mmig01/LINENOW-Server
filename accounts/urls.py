from django.urls import path, include
from .views import *
from dj_rest_auth.views import LoginView, LogoutView

app_name = 'accounts'

urlpatterns = [
    # 일반 로그인 / 회원가입
    path('accounts/login', LoginView.as_view(), name='login'),
    path('accounts/logout', LogoutView.as_view(), name='logout'),
    path('accounts/registration', include('dj_rest_auth.registration.urls')),
    # path('dj-rest-auth/', include('dj_rest_auth.urls')),
    # path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),    
    # path('allauth/', include('allauth.urls')),

    # 회원 탈퇴
    path('accounts/withdraw', WithdrawUserView.as_view(), name='withdraw'),
]