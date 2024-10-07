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
from dj_rest_auth.registration.views import RegisterView
from .forms import CustomSignupForm


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

class CustomRegisterView(RegisterView):
    form_class = CustomSignupForm  # Turnstile이 적용된 폼을 사용

    def create(self, request, *args, **kwargs):
        print(request.data)
        response = super().create(request, *args, **kwargs)
        return response