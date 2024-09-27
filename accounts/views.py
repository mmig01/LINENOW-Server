from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.kakao import views as kakao_view
import requests
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from utils.responses import custom_response
from utils.exceptions import *
from django.conf import settings

BACK_BASE_URL = settings.BACK_BASE_URL
KAKAO_CALLBACK_URI = BACK_BASE_URL + settings.KAKAO_CALLBACK_URI

@api_view(["GET"])
@permission_classes([AllowAny])
def kakao_callback(request):
    client_id = settings.KAKAO_CLIENT_ID
    code = request.GET.get("code")

    # code로 access token 요청
    token_req = requests.get(f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={client_id}&redirect_uri={KAKAO_CALLBACK_URI}&code={code}")
    token_req_json = token_req.json()

    error = token_req_json.get("error", None)
    
    if error is not None:
        raise InvalidToken("The access token from Kakao was invalid.")

    kakao_access_token = token_req_json.get("access_token")
    
    # 프로필 정보 요청
    profile_request = requests.get("https://kapi.kakao.com/v2/user/me", headers={"Authorization": f"Bearer {kakao_access_token}"})
    profile_json = profile_request.json()
    
    kakao_account = profile_json.get('kakao_account')
    email = kakao_account.get('email', None)
    
    try:
        user = User.objects.get(email=email)
        
        # 기존에 kakao로 가입된 유저
        data = {"access_token": kakao_access_token, "code": code}
        accept = requests.post(f"{BACK_BASE_URL}api/v1/accounts/kakao/login/finish/", data=data)
        accept_status = accept.status_code
        

        if accept_status != 200:
            return InvalidToken("Login Failed.")

        accept_json = accept.json()

        # refresh_token을 headers 문자열에서 추출
        refresh_token = accept.cookies.get('refresh_token')
        if not refresh_token:
            raise InvalidToken("Failed to retrieve refresh token.")
        
        access_token = accept_json['access']
        
        data = {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

        return custom_response(data=data, message="Login successful.", code=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        
        # 기존에 가입된 유저가 없으면 새로 가입
        data = {"access_token": kakao_access_token, "code": code}
        accept = requests.post(f"{BACK_BASE_URL}api/v1/accounts/kakao/login/finish/", data=data)
        accept_status = accept.status_code
        
        if accept_status != 200:
            return InvalidToken("Signup Failed.")
    
        accept_json = accept.json()
        tokens = requests.post(f"{BACK_BASE_URL}api/v1/dj-rest-auth/registration/", data=data)
        
        # refresh_token을 headers 문자열에서 추출
        refresh_token = accept.cookies.get('refresh_token')
        if not refresh_token:
            raise InvalidToken("Failed to retrieve refresh token.")
        
        data = {
            "access_token": access_token,
            "refresh_token":refresh_token,
        }
        return custom_response(data=data, message="Signup successful.", code=status.HTTP_200_OK)
    
class KakaoLogin(SocialLoginView):
    adapter_class = kakao_view.KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = KAKAO_CALLBACK_URI
