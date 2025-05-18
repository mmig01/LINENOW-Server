from django.utils import timezone
import random
import os
import requests
import hashlib
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .models import SMSAuthenticate, User, CustomerUser
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
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            user_phone = validated_data.get('user_phone')
            provided_sms_code = validated_data.get('sms_code')
            privided_sms_code_hash = hashlib.sha256(provided_sms_code.encode('utf-8')).hexdigest()
            # SMS 인증 코드 유효성 검사
            try:
                # 해당 전화번호의 최신 인증 기록을 가져옵니다.
                sms_instance = SMSAuthenticate.objects.filter(user_phone=user_phone).latest('created_at')
            except SMSAuthenticate.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "문자인증 실패",
                    "code": 400,
                    "data": [{"detail": "해당 전화번호의 인증 기록이 존재하지 않습니다."}]
                }, status=status.HTTP_400_BAD_REQUEST)

            # 인증 코드 일치와 유효 기간(예: 1분 이내) 검사
            if sms_instance.sms_code != privided_sms_code_hash or sms_instance.is_expired():
                return Response({
                    "status": "error",
                    "message": "문자인증 실패",
                    "code": 400,
                    "data": [{"detail": "문자인증코드가 올바르지 않거나 만료되었습니다."}]
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                # 인증 통과 시 회원가입 진행
                user = serializer.save()
                
            except Exception as e:
                return Response({
                    "status": "error",
                    "message": "회원가입 실패",
                    "code": 500,
                    "data": [
                        {"detail": str(e)}
                    ]
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            customer_user = CustomerUser.objects.create(user=user)
            refresh = RefreshToken.for_user(customer_user.user)
            data = {
                "status": "success",
                "message": "회원가입 성공",
                "code": 200,
                "data": [
                    {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "user": {
                            "user_id": customer_user.id,
                            "user_name": customer_user.user.user_name,
                            "user_phone": customer_user.user.user_phone,
                            "no_show_num": customer_user.no_show_num
                        }
                    }
                ]
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            error = {}
            for field, error_list in serializer.errors.items():
                for error in error_list:
                    # error는 ErrorDetail 객체입니다.
                    error = {"detail": f"{field}: {error}"}
            return Response({
                "status": "error",
                "message": "회원가입 실패",
                "code": 500,
                "data": [
                   error
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
        customer_user = get_object_or_404(CustomerUser, user=user)
        if customer_user.user.check_password(password):
            refresh = RefreshToken.for_user(customer_user.user)
            data = {
                "status": "success",
                "message": "로그인 성공",
                "code": 200,
                "data": [
                    {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "user": {
                            "user_id": customer_user.id,
                            "user_name": customer_user.user.user_name,
                            "user_phone": customer_user.user.user_phone,
                            "no_show_num": customer_user.no_show_num
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
        # access 토큰을 통한 인증이 필요
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "인증이 필요합니다.",
                "code": 401,
                "data": [
                    {"detail": "유효한 access 토큰이 필요합니다."}
                ]
            }, status=status.HTTP_401_UNAUTHORIZED)
        
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
        
        # 블랙리스트 처리
        tokens = OutstandingToken.objects.filter(user=request.user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
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
            CustomerUser.objects.all().update(no_show_num=0)
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
        
    @action(detail=False, methods=['get'], url_path='blackuser')
    def is_black_user(self, request):
         # access 토큰을 통한 인증이 필요
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "인증이 필요합니다.",
                "code": 401,
                "data": [
                    {"detail": "유효한 access 토큰이 필요합니다."}
                ]
            }, status=status.HTTP_401_UNAUTHORIZED)
        user = request.user
        customer_user = get_object_or_404(CustomerUser, user=user)
        if customer_user.no_show_num >= 2:
            return Response({
                "status": "success",
                "message": "블랙리스트 사용자입니다.",
                "code": 200,
                "data": [
                    {"is_black_user": True}
                ]
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "success",
                "message": "정상 사용자입니다.",
                "code": 200,
                "data": [
                    {"is_black_user": False}
                ]
            }, status=status.HTTP_200_OK)
        
class SMSViewSet(viewsets.ViewSet):
    """
    문자인증 관련 API 뷰
    - POST /sms/send/   : 전화번호에 인증 코드를 전송
    - POST /sms/verify/ : 전화번호와 인증 코드를 검증
    """
    @action(detail=False, methods=['post'], url_path='message')
    def send_sms(self, request):
        user_phone = request.data.get('user_phone')
        if not user_phone:
            return Response({
                "status": "error",
                "message": "문자인증 실패",
                "code": 400,
                "data": [{"detail": "전화번호가 필요합니다."}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # User 에 user_phone 이 존재하는지 확인
        if User.objects.filter(user_phone=user_phone).exists() == True:
            return Response({
                "status": "error",
                "message": "문자인증 실패",
                "code": 400,
                "data": [{"detail": "이미 가입된 전화번호입니다."}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # SMSAuthenticate 객체 생성 또는 업데이트
        try:
            sms_token_key = os.getenv("SMS_TOKEN_KEY")
            sms_api_key = os.getenv("SMS_API_KEY")
            send_phone = os.getenv("SEND_PHONE")
            ssodaa_base_url = os.getenv("SSODAA_BASE_URL")
            sms_code = str(random.randint(10000, 99999))
    
            payload = {
                'token_key': sms_token_key,
                'msg_type': 'SMS',
                'dest_phone': user_phone,
                'send_phone': send_phone,
                'msg_body': f"라인나우 인증코드: {sms_code}",
            }
            headers = {
                'x-api-key': sms_api_key,
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            response = requests.post(
                ssodaa_base_url	+ "/sms/send/sms",   # 
                json=payload,      # JSON body
                headers=headers,   # 인증 헤더
                timeout=5          # 과도한 지연 방지용 타임아웃 
            )
            response.raise_for_status()  # 200 이외 코드는 예외 발생
            
            SMSAuthenticate.objects.update_or_create(
                user_phone=user_phone,
                defaults={'sms_code': hashlib.sha256(sms_code.encode('utf-8')).hexdigest(), 'created_at': timezone.now()}
            )
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "오류",
                "code": 500,
                "data": [{"detail": str(e)}]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "status": "success",
            "message": "문자인증 코드가 전송되었습니다.",
            "code": 200,
        }, status=status.HTTP_200_OK)