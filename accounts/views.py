from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ViewSet):
    """
    - POST   /user/registration/ -> 회원가입 (user_name, user_phone, sms_code, user_password1, user_password2)
    - POST   /user/login/        -> 로그인
    - DELETE /user/{pk}/withdraw  -> 회원탈퇴
    """
    
    # 회원가입
    @action(detail=False, methods=['post'], url_path='registration')
    def sign_up(self, request):
        """
        프론트엔드로부터 user_name, user_phone, sms_code, user_password1, user_password2를 받고,
        패스워드 일치 여부를 검사한 후 회원가입을 진행합니다.
        """
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()  # 시리얼라이저 create()에서 패스워드 일치, sms_code 등 검증 후 저장
            refresh = RefreshToken.for_user(user)
            data = {
                "status": "success",
                "message": "회원가입 성공",
                "code": 200,
                "data": [
                    {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "user": {
                            "user_id": user.id,
                            "user_name": user.user_name,
                            "user_phone": user.user_phone,
                            "no_show_num": user.no_show_num
                        }
                    }
                ]
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": "error",
                "message": "회원가입 실패",
                "code": 500,
                "data": [
                    {"detail": "모든 필드를 정확히 입력해주세요."}
                ]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 로그인
    @action(detail=False, methods=['post'], url_path='login')
    def sign_in(self, request):
        phone = request.data.get('user_phone')
        password = request.data.get('user_password')
    
        if not phone or not password:
            return Response({
                "status": "error",
                "message": "로그인 실패",
                "code": 400,
                "data": [
                    {"detail": "전화번호와 비밀번호를 모두 입력해주세요."}
                ]
            }, status=status.HTTP_400_BAD_REQUEST)
    
        user = get_object_or_404(User, user_phone=phone)
    
        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            data = {
                "status": "success",
                "message": "로그인 성공",
                "code": 200,
                "data": [
                    {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "user": {
                            "user_id": user.id,
                            "user_name": user.user_name,
                            "user_phone": user.user_phone,
                            "no_show_num": user.no_show_num
                        }
                    }
                ]
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "로그인 실패",
                "code": 401,
                "data": [
                    {"detail": "비밀번호가 올바르지 않습니다."}
                ]
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
         # access 토큰을 통한 인증이 필요함 (DRF JWT Authentication이 설정되어 있다면 request.user가 채워짐)
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "인증이 필요합니다.",
                "code": 401,
                "data": [
                    {"detail": "유효한 access 토큰이 필요합니다."}
                ]
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # access 토큰에 해당하는 사용자 삭제
        request.user.delete()
        return Response({
            "status": "success",
            "message": "로그아웃이 완료되었습니다.",
            "code": 200,
            "data": [
                {"detail": "로그아웃이 완료되었습니다."}
            ]
        }, status=status.HTTP_200_OK)
        
        

    @action(detail=False, methods=['delete'], url_path='withdraw')
    def withdraw(self, request):
        # access 토큰을 통한 인증이 필요함 (DRF JWT Authentication이 설정되어 있다면 request.user가 채워짐)
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "인증이 필요합니다.",
                "code": 401,
                "data": [
                    {"detail": "유효한 access 토큰이 필요합니다."}
                ]
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # access 토큰에 해당하는 사용자 삭제
        request.user.delete()
        return Response({
            "status": "success",
            "message": "회원탈퇴가 완료되었습니다.",
            "code": 200,
            "data": [
                {"detail": "회원탈퇴가 완료되었습니다."}
            ]
        }, status=status.HTTP_200_OK)
        
        # 모든 유저의 no_show_num 값을 0으로 초기화하는 액션
    @action(detail=False, methods=['post'], url_path='reset-no-show')
    def reset_no_show_num(self, request):
        try:
            User.objects.all().update(no_show_num=0)
            return Response({
                "status": "success",
                "message": "모든 유저의 no_show_num 값이 0으로 초기화되었습니다.",
                "code": 200,
                "data": [
                    {"detail": "초기화 완료"}
                ]
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": "error",
                "message": "초기화 실패",
                "code": 500,
                "data": [
                    {"detail": str(e)}
                ]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)