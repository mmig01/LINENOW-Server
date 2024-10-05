from rest_framework import mixins, viewsets, filters
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
from utils.mixins import CustomResponseMixin
from django_filters.rest_framework import DjangoFilterBackend
from .filters import WaitingFilter
from rest_framework.decorators import action
from waiting.tasks import check_ready_to_confirm

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

# 부스 웨이팅 조회
class BoothWaitingViewSet(CustomResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BoothWaitingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = WaitingFilter
    ordering_fields = ['created_at']  # 대기 생성 시간 순으로 정렬

    def get_queryset(self):
        jwt_authenticator = JWTAuthentication()
        result = jwt_authenticator.authenticate(self.request)

        if result is None:
            return None
        
        user, token = result
        admin = get_object_or_404(Admin, user=user)
        booth = admin.booth

        # 해당 부스의 대기 목록 반환
        return Waiting.objects.filter(booth=booth).order_by('created_at')
    
    @action(detail=True, methods=['post'], url_path='action')
    def action(self, request, *args, **kwargs):
        """
        웨이팅 상태를 변경하는 POST 메서드 (action 기반)
        request body: {"action": "call", "confirm", "cancel"}
        """
        jwt_authenticator = JWTAuthentication()
        result = jwt_authenticator.authenticate(request)

        if result is None:
            return custom_response(
                data=None,
                message="Unauthorized.",
                code=status.HTTP_401_UNAUTHORIZED,
                success=False
            )

        user, token = result
        admin = get_object_or_404(Admin, user=user)
        booth = admin.booth

        # 대기 상태 변경할 대상 가져오기
        waiting_id = kwargs.get('pk')
        waiting = get_object_or_404(Waiting, id=waiting_id, booth=booth)

        # request body에서 action 값을 가져옴
        action = request.data.get('action', None)

        if action == 'call':
            if waiting.waiting_status != 'waiting':
                return custom_response(
                    data=None,
                    message="Cannot call team while it is not waiting.",
                    code=status.HTTP_400_BAD_REQUEST,
                    success=False
                )
            waiting.waiting_status = 'ready_to_confirm'
            waiting.ready_to_confirm_at = timezone.now()
            check_ready_to_confirm.apply_async((waiting.id,), countdown=180)  # 3분 후 Task 실행
        elif action == 'confirm':
            waiting.waiting_status = 'arrived'
            waiting.confirmed_at = timezone.now()
        elif action == 'cancel':
            waiting.waiting_status = 'canceled'
            waiting.canceled_at = timezone.now()
        else:
            return custom_response(
                data=None,
                message="Invalid action.",
                code=status.HTTP_400_BAD_REQUEST,
                success=False
            )

        waiting.save()
        
        serializer = BoothWaitingSerializer(waiting)
        return custom_response(
            data=serializer.data,
            message=f"Waiting status updated to {waiting.waiting_status} successfully!",
            code=status.HTTP_200_OK
        )



# 부스 관리 
class BoothDetailViewSet(CustomResponseMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'update':
            return BoothDetailSerializer
        return BoothSerializer

    def get_queryset(self):
        jwt_authenticator = JWTAuthentication()
        result = jwt_authenticator.authenticate(self.request)

        if result is None:
            return None
        
        user, token = result
        admin = get_object_or_404(Admin, user=user)
        booth = admin.booth

        return Booth.objects.filter(id=booth.id)
    
    def update(self, request, *args, **kwargs):
        jwt_authenticator = JWTAuthentication()
        result = jwt_authenticator.authenticate(request)

        if result is None:
            return custom_response(
                data=None,
                message="Unauthorized.",
                code=status.HTTP_401_UNAUTHORIZED,
                success=False
            )

        user, token = result
        admin = get_object_or_404(Admin, user=user)
        booth = admin.booth

        # status 필드가 올바른지 검사, 변수명 충돌을 피하기 위해 _status로 변경
        _status = request.data.get('status', None)
        # 부스 정보 업데이트
        try:
            serializer = BoothDetailSerializer(booth, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)  # raise_exception=True로 유효성 검사를 바로 처리
            serializer.save()
            
            return custom_response(
                data=serializer.data,
                message="Booth information updated successfully.",
                code=status.HTTP_200_OK
            )
        except serializers.ValidationError as e:
            # 유효성 검사 중 발생한 에러를 400 응답으로 반환
            return custom_response(
                data=e.detail,
                message="Validation error.",
                code=status.HTTP_400_BAD_REQUEST,
                success=False
            )

        except Exception as e:
            # 예상하지 못한 예외 발생 시에도 500 에러 대신 상세한 에러 메시지를 반환
            return custom_response(
                data=str(e),
                message="An unexpected error occurred.",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )
        
    # 부스 대기 상태 변경 endpoint 2개로 분리
    @action(detail=True, methods=['post'], url_path='pause')
    def pause(self, request, *args, **kwargs):
        """
        부스의 대기 상태를 'paused'로 변경.
        특정 상태에서는 전환할 수 없음 ('not_started', 'finished', 'paused').
        """
        jwt_authenticator = JWTAuthentication()
        result = jwt_authenticator.authenticate(request)

        if result is None:
            return custom_response(
                data=None,
                message="Unauthorized.",
                code=status.HTTP_401_UNAUTHORIZED,
                success=False
            )

        user, token = result
        admin = get_object_or_404(Admin, user=user)
        booth = admin.booth

        # 'not_started', 'finished', 'paused' 상태에서는 'paused'로 전환할 수 없음
        if booth.is_operated in ['not_started', 'finished', 'paused']:
            return custom_response(
                data=None,
                message=f"Cannot pause booth while it is {booth.is_operated}.",
                code=status.HTTP_400_BAD_REQUEST,
                success=False
            )

        # 대기 상태를 'paused'로 변경
        booth.is_operated = 'paused'
        booth.save()

        return custom_response(
            data={'status': booth.is_operated},
            message="Booth waiting status changed to paused.",
            code=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='resume')
    def resume(self, request, *args, **kwargs):
        """
        부스의 대기 상태를 'operating'으로 변경.
        특정 상태에서는 전환할 수 없음 ('not_started', 'finished', 'operating').
        """
        jwt_authenticator = JWTAuthentication()
        result = jwt_authenticator.authenticate(request)

        if result is None:
            return custom_response(
                data=None,
                message="Unauthorized.",
                code=status.HTTP_401_UNAUTHORIZED,
                success=False
            )

        user, token = result
        admin = get_object_or_404(Admin, user=user)
        booth = admin.booth

        # 'not_started', 'finished', 'operating' 상태에서는 'operating'으로 전환할 수 없음
        if booth.is_operated in ['not_started', 'finished', 'operating']:
            return custom_response(
                data=None,
                message=f"Cannot resume booth while it is {booth.is_operated}.",
                code=status.HTTP_400_BAD_REQUEST,
                success=False
            )

        # 대기 상태를 'operating'으로 변경
        booth.is_operated = 'operating'
        booth.save()

        return custom_response(
            data={'status': booth.is_operated},
            message="Booth waiting status changed to operating.",
            code=status.HTTP_200_OK
        )
    # @action(detail=True, methods=['post'], url_path='call')

# 부스 전체 대기 목록 조회
class BoothWaitingListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            jwt_authenticator = JWTAuthentication()
            result = jwt_authenticator.authenticate(request)

            if result is None:
                return custom_response(data=None, message="Unauthorized.", code=status.HTTP_401_UNAUTHORIZED, success=False)
            
            user, token = result
            admin = get_object_or_404(Admin, user=user)  # 로그인한 관리자 정보
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
    permission_classes = [IsAuthenticated]
    def get(self, request, status_group):
        try:
            jwt_authenticator = JWTAuthentication()
            result = jwt_authenticator.authenticate(request)

            if result is None:
                return custom_response(data=None, message="Unauthorized.", code=status.HTTP_401_UNAUTHORIZED, success=False)
            user, token = result

            admin = get_object_or_404(Admin, user = user)  # 로그인한 관리자 정보
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