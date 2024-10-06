from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .models import User
import jwt
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

class WithdrawUserView(APIView) :
    def post(self,req):
        token = req.headers.get('Authorization')  # 헤더에서 Authorization 값 가져오기
        print(token)
        if not token:
            raise AuthenticationFailed('Access token is missing or invalid')
        if token.startswith('Bearer '):
            token = token.split(' ')[1]

        try:
            # 토큰 디코딩
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Access token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid access token')

        # 유저 확인
        if payload['user_id'] != req.user.id:
            raise AuthenticationFailed('User does not match the token')

        # 유저 삭제
        user = req.user
        user.delete()

        res = Response({"message": "User delete success"})
        res.delete_cookie('access_token')
        res.delete_cookie('refresh_token')
        return res