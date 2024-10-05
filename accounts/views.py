import json, requests
from django.views.decorators.csrf import csrf_exempt
from utils.responses import custom_response
from rest_framework.response import Response
from django.shortcuts import redirect
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from rest_framework import status
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.kakao import views as kakao_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.models import SocialAccount
from .models import User
from rest_framework.decorators import api_view

from rest_framework.permissions import IsAuthenticated

BACK_BASE_URL = settings.BACK_BASE_URL

REDIRECT_URL = f'{BACK_BASE_URL}api/v1/accounts/kakao/callback/'

@api_view(['GET'])
def kakao_login(request):
    rest_api_key = getattr(settings, 'KAKAO_CLIENT_ID')
    
    return redirect(
        f"https://kauth.kakao.com/oauth/authorize?client_id={rest_api_key}&redirect_uri={REDIRECT_URL}&response_type=code&prompt=login"
    )

@api_view(['GET'])
@csrf_exempt
def kakao_callback(request):
    rest_api_key = getattr(settings, 'KAKAO_CLIENT_ID')
    # 프론트로부터 받은 코드
    code = request.GET.get("code")
    print("code : " , code)
    # 프론트 주소
    redirect_uri = REDIRECT_URL
    
    #Access Token Request
    token_req = requests.get(
        f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={rest_api_key}&redirect_uri={redirect_uri}&code={code}")
    token_req_json = token_req.json()

    print("token JSON:", json.dumps(token_req_json, indent=4, ensure_ascii=False))
    error = token_req_json.get("error")
    if error is not None:
        return custom_response(data=None, message="token error", code=status.HTTP_400_BAD_REQUEST, success=False)
    access_token = token_req_json.get("access_token")
    
    #Email Request
    profile_request = requests.get(
        "https://kapi.kakao.com/v2/user/me", headers={"Authorization": f"Bearer {access_token}"})
    profile_json = profile_request.json()

    print("Profile JSON:", json.dumps(profile_json, indent=4, ensure_ascii=False))
    error = profile_json.get("error")
    if error is not None:
        return custom_response(data=None, message="profile error", code=status.HTTP_400_BAD_REQUEST, success=False)
    
    kakao_account = profile_json.get('kakao_account')
    # 사용자의 정보
    properties = profile_json.get('properties')

    email = kakao_account.get('email')
    name = properties.get('nickname')

    """
    Signup or Signin Request
    """
    try:
        user = User.objects.get(email=email)
        # 기존에 가입된 유저의 Provider가 kakao가 아니면 에러 발생, 맞으면 로그인
        # 다른 SNS로 가입된 유저
        social_user = SocialAccount.objects.get(user=user)
        if social_user is None:
            return custom_response(data=None, message="email exists but not social user", code=status.HTTP_400_BAD_REQUEST, success=False)
        if social_user.provider != 'kakao':
            return custom_response(data=None, message="no matching social type", code=status.HTTP_400_BAD_REQUEST, success=False)
        # 기존에 kakao로 가입된 유저
        data = {'access_token': access_token, 'code': code}
        accept = requests.post(
            f"{BACK_BASE_URL}/api/v1/accounts/kakao/login/finish/", data=data)
        
        accept_status = accept.status_code

        print("try 에서 출력한 status 값 : " , accept_status)

        if accept_status != 200:
            return custom_response(data=None, message="failed to sign in", code=status.HTTP_400_BAD_REQUEST, success=False)
        accept_json = accept.json()
        
        userinfo = {
            "email" : user.email,
            'name' : user.username
        }
        accept_json.pop('user', None)
        accept_json['userinfo'] = userinfo
        
        return custom_response(message="Login successful", code=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        # 기존에 가입된 유저가 없으면 새로 가입
        data = {'access_token': access_token, 'code': code}
        accept = requests.post(
            f"{BACK_BASE_URL}/api/v1/accounts/kakao/login/finish/", data=data)
        accept_status = accept.status_code
        if accept_status != 200:
            return custom_response(data=None, message="failed to sign up", code=status.HTTP_400_BAD_REQUEST, success=False)
        
        user = User.objects.get(email=email)
        user.name = name
        user.save()
        # Access Token, Refresh token 
        accept_json = accept.json()
        userinfo = {
            "email" : user.email,
            'name' : user.username
        }
        accept_json.pop('user', None)
        accept_json['userinfo'] = userinfo
        return custom_response(message="Signin successful", code=status.HTTP_200_OK)

import traceback

class KakaoLogin(SocialLoginView):
    adapter_class = kakao_view.KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = BACK_BASE_URL

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return response

        except Exception as e:
            # 전체 트레이스백을 출력
            error_message = f"Error occurred in KakaoLogin post method: {str(e)}"
            traceback.print_exc()

            return Response(
                {"detail": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )