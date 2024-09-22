from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from django.shortcuts import redirect
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.kakao import views as kakao_view
from django.http import JsonResponse
import requests
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from json.decoder import JSONDecodeError
import os
import environ

BASE_URL = 'http://211.188.52.202/'
KAKAO_CALLBACK_URI = BASE_URL + 'api/v1/accounts/kakao/callback/'

@api_view(["GET"])
@permission_classes([AllowAny])
def kakao_callback(request):
    client_id = os.environ.get("KAKAO_CLIENT_ID")
    code = request.GET.get("code")

    # code로 access token 요청
    token_req = requests.get(f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={client_id}&redirect_uri={KAKAO_CALLBACK_URI}&code={code}")
    token_req_json = token_req.json()

    error = token_req_json.get("error", None)
    if error is not None:
        raise JSONDecodeError(error)

    access_token = token_req_json.get("access_token")
    
    # 프로필 정보 요청
    profile_request = requests.get("https://kapi.kakao.com/v2/user/me", headers={"Authorization": f"Bearer {access_token}"})
    profile_json = profile_request.json()
    
    kakao_account = profile_json.get('kakao_account')
    email = kakao_account.get('email', None)

    try:
        user = User.objects.get(email=email)
        
        # 기존에 kakao로 가입된 유저
        data = {"access_token": access_token, "code": code}
        accept = requests.post(f"{BASE_URL}accounts/kakao/login/finish/", data=data)
        accept_status = accept.status_code
        if accept_status != 200:
            return JsonResponse({"err_msg": "failed to signin"}, status=accept_status)
        accept_json = accept.json()
        # refresh_token을 headers 문자열에서 추출
        refresh_token = accept.headers['Set-Cookie']
        refresh_token = refresh_token.replace('=',';').replace(',',';').split(';')
        token_index = refresh_token.index(' refresh_token')
        cookie_max_age = 3600 * 24 * 14 # 14일
        refresh_token = refresh_token[token_index+1]
        accept_json.pop("user", None)
        response_cookie = JsonResponse(accept_json)
        response_cookie.set_cookie('refresh_token', refresh_token, max_age=cookie_max_age, httponly=True, samesite='Lax')
        return response_cookie
    
    except User.DoesNotExist:

        # 기존에 가입된 유저가 없으면 새로 가입
        data = {"access_token": access_token, "code": code}
        accept = requests.post(f"{BASE_URL}accounts/kakao/login/finish/", data=data)
        accept_status = accept.status_code
        if accept_status != 200:
            return JsonResponse({"err_msg": "failed to signup"}, status=accept_status)
    
        accept_json = accept.json()

        # refresh_token을 headers 문자열에서 추출
        refresh_token = accept.headers['Set-Cookie']
        refresh_token = refresh_token.replace('=',';').replace(',',';').split(';')
        token_index = refresh_token.index(' refresh_token')
        refresh_token = refresh_token[token_index+1]

        accept_json.pop("user", None)
        response_cookie = JsonResponse(accept_json)
        response_cookie.set_cookie('refresh_token', refresh_token, max_age=cookie_max_age, httponly=True, samesite='Lax')
        return response_cookie

class KakaoLogin(SocialLoginView):
    adapter_class = kakao_view.KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = KAKAO_CALLBACK_URI