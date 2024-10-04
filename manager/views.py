from rest_framework import mixins, viewsets
from rest_framework.response import Response
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from utils.responses import custom_response
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# FAQ 리스트 조회만 가능한 ViewSet
class FAQViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    
    
# 관리자 로그인
@method_decorator(csrf_exempt, name='dispatch')
class AdminLoginView(APIView):
    def post(self, request):
        admin_code = request.data.get('admin_code')
        
        try:
            admin = Admin.objects.get(admin_code=admin_code)
            user = admin.user
        except Admin.DoesNotExist:
            # 고유번호가 틀렸을 때
            return custom_response(data=None, message="Invalid admin code. Please check and try again.", code=status.HTTP_400_BAD_REQUEST, success=False)
        
        # 로그인 처리 (세션 or 토큰 저장 등)
        # request.session['admin_id'] = admin.id  # 세션에 관리자 ID 저장

        # token 사용
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        booth_name = admin.booth.name if admin.booth else "No booth assigned"
        return custom_response(data={
            'booth_name': booth_name,
            'access_token': access_token,
            'refresh_token': str(refresh)
            }, message=f"Login Success !!! Hi, {booth_name} manager.", code=status.HTTP_200_OK)
        
        # # 쿠키 설정
        # response.set_cookie(
        #     key='access_token',
        #     value=access_token,
        #     httponly=True,  # 자바스크립트로 접근 불가
        #     secure=False,    # HTTPS에서만 전송 (개발 환경에서는 False)
        #     samesite='Lax'  # 같은 사이트에서만 쿠키 전송 (보안 강화)
        # )
        # response.set_cookie(
        #     key='refresh_token',
        #     value=str(refresh),
        #     httponly=True,
        #     secure=True,
        #     samesite='Lax'
        # )
# 관리자 로그아웃
class AdminLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        # admin_id = request.session.get('admin_id')
        
        # if admin_id:
        #     # 세션에서 admin_id를 이용해 관리자 정보를 가져옴
        #     admin = get_object_or_404(Admin, id=admin_id)
        #     booth_name = admin.booth.name if admin.booth else "No booth assigned"
            
        #     # 세션 삭제로 로그아웃 처리
        #     request.session.flush()
            
        #     return custom_response(data={'booth_name': booth_name}, message=f"Successfully logged out from {booth_name}.", code=status.HTTP_200_OK)
        
        # return custom_response(data=None, message="No active session found to log out.", code=status.HTTP_400_BAD_REQUEST, success=False)
        try:
            # JWT 토큰을 통해 현재 로그인한 사용자 가져오기
            # 쿠키 기반 JWT 인증
            jwt_authenticator = JWTAuthentication()
            result = jwt_authenticator.authenticate(request)

            # 인증 실패 시
            if result is None:
                return custom_response(data=None, message="Unauthorized.", code=status.HTTP_401_UNAUTHORIZED, success=False)

            user, token = result  # 사용자와 토큰을 받아옴

            # 현재 User와 연결된 Admin 객체 가져오기
            admin = get_object_or_404(Admin, user=user)
            booth_name = admin.booth.name if admin.booth else "No booth assigned"
            
            # refresh_token 가져오기
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return custom_response(data=None, message="Refresh token not provided.", code=status.HTTP_400_BAD_REQUEST, success=False)
            
            # refresh_token을 블랙리스트 처리
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()  # refresh 토큰을 블랙리스트에 추가하여 무효화
            except Exception as e:
                return custom_response(data=None, message="Invalid refresh token.", code=status.HTTP_400_BAD_REQUEST, success=False)
            
            return custom_response(data={'booth_name': booth_name}, message="Successfully logged out from {booth_name}", code=status.HTTP_200_OK)
        
        except Exception as e:
            return custom_response(data=None, message=str(e), code=status.HTTP_400_BAD_REQUEST, success=False)

# 부스 전체 대기 목록 조회
class BoothWaitingListView(APIView):
    def get(self, request):
        try:
            admin_id = request.session.get('admin_id')  # 세션에서 관리자 ID 가져오기
            
            if not admin_id:
                return custom_response(data=None, message="You must be logged in as an admin to view reservations.", code=status.HTTP_403_FORBIDDEN, success=False)
            
            admin = get_object_or_404(Admin, id=admin_id)  # 로그인한 관리자 정보
            booth = admin.booth  # 해당 관리자가 관리하는 부스 정보 가져올 수 있도록 !!
            
            # 해당 부스의 모든 대기 정보 조회
            waitings = Waiting.objects.filter(booth=booth).order_by('created_at')  # 대기 생성 시간 순으로 정렬(오래된 순)
            serializer = BoothWaitingSerializer(waitings, many=True)
            
            return custom_response(data=serializer.data, message="Booth waiting status fetched successfully", code=status.HTTP_200_OK)
        
        except ObjectDoesNotExist:
            return custom_response(data=None, message="Admin or booth not found.", code=status.HTTP_404_NOT_FOUND, success=False)
        except Exception as e:
            # 모든 다른 예외에 대해서도 500 에러 대신 명확한 메시지를 반환!
            return custom_response(data=None, message=str(e), code=status.HTTP_500_INTERNAL_SERVER_ERROR, success=False)

    
# 웨이팅 상태별 필터링
class BoothWaitingStatusFilterView(APIView):
    def get(self, request, status_group):
        try:
            admin_id = request.session.get('admin_id')  # 세션에서 관리자 ID 가져오기
            
            if not admin_id:
                return custom_response(data=None, message="You must be logged in as an admin to view reservations.", code=status.HTTP_403_FORBIDDEN, success=False)
            
            admin = get_object_or_404(Admin, id=admin_id)  # 로그인한 관리자 정보
            booth = admin.booth
            
            # 상태별 필터링 로직
            if status_group == 'waiting':
                waitings = Waiting.objects.filter(booth=booth, waiting_status='waiting').order_by('created_at')
            elif status_group == 'calling':
                waitings = Waiting.objects.filter(booth=booth, waiting_status__in=['ready_to_confirm', 'confirmed']).order_by('created_at')
            elif status_group == 'arrived':
                waitings = Waiting.objects.filter(booth=booth, waiting_status='arrived').order_by('created_at')
            elif status_group == 'canceled':
                waitings = Waiting.objects.filter(booth=booth, waiting_status__in=['canceled', 'time_over_canceled']).order_by('created_at')
            else:
                return custom_response(data=None, message="Invalid status group.", code=status.HTTP_400_BAD_REQUEST, success=False)

            serializer = BoothWaitingSerializer(waitings, many=True)
            return custom_response(data=serializer.data, message=f"Booth waiting status ({status_group}) fetched successfully", code=status.HTTP_200_OK)

        except Exception as e:
            # 500 에러 대신 상세한 예외 메시지를 반환!
            return custom_response(data=None, message=f"An error occurred: {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR, success=False)