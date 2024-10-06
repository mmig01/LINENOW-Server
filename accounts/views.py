from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .models import User
import jwt
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from utils.responses import custom_response

class WithdrawUserView(APIView) :
    def post(self,req):

        user = req.user
        refresh_token = req.data.get('refresh_token')
        if not refresh_token:
            return custom_response(data=None, message="Refresh token not provided.",
                                    code=status.HTTP_400_BAD_REQUEST, success=False)

        # 유저 삭제
        user.delete()

        res = Response({"message": "User delete success"})

        return res