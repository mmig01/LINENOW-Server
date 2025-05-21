from rest_framework.response import Response
from rest_framework import mixins, viewsets
from .models import *
from .serializers import *
from utils.responses import custom_response

from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Value, IntegerField

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import action
# from waiting.tasks import check_ready_to_confirm

# Ask 리스트 조회만 가능한 ViewSet
class AskViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Ask.objects.all()
    serializer_class = AskSerializer
    

class ManagerViewSet(viewsets.ViewSet):
    """
    manager_code 인증 후 JWT 토큰 발급
    POST /manager/login/
    {
      "manager_code": "abcd1234"
    }
    """
    def get_booth_queryset(self, request, statuses):
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "인증이 필요합니다.",
                "code": 401,
                "data": [{"detail": "유효한 access 토큰이 필요합니다."}]
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not request.user.is_manager:
            return custom_response(
                data={'detail': "관리자 유저가 아닙니다."},
                message='권한이 없습니다.',
                code=403,
                success=False
            )

        try:
            booth = request.user.manager_user.booth
            queryset = Waiting.objects.filter(booth=booth, waiting_status__in=statuses).order_by('created_at')
            serializer = ManagerWaitingListSerializer(queryset, many=True)
            return custom_response(
                serializer.data,
                message='관리자 부스 대기 조회 성공',
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)},
                message='관리자 부스 대기 조회 실패',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )
     # 회원가입
    @action(detail=False, methods=['post'], url_path='registration')
    def sign_up(self, request):
        serializer = ManagerSerializer(data=request.data)
        if serializer.is_valid():
            try:
                booth = request.data.get('booth')
                manager_booth = get_object_or_404(Booth, booth_name=booth)
                
                user = serializer.save()
                manager_user = Manager.objects.create(user=user, booth=manager_booth)
                manager_user.user.is_manager = True
                user.save()
            except Exception as e:
                return Response({
                    "status": "error",
                    "message": "회원가입 실패",
                    "code": 500,
                    "data": [
                        {"detail": str(e)}
                    ]
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

            refresh = RefreshToken.for_user(manager_user.user)
            data = {
                "status": "success",
                "message": "회원가입 성공",
                "code": 200,
                "data": [
                    {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "user": {
                            "user_id": manager_user.id,
                            "user_name": manager_user.user.user_name
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
        manager_code = request.data.get('manager_code')
        if not manager_code:
            return Response({
                "status": "error",
                "message": "로그인 실패",
                "code": 400,
                "data": [
                    {"detail": "관리자 코드를 입력해주세요."}
                ]
            }, status=status.HTTP_400_BAD_REQUEST)
        

        candidate = Manager.objects.all()
        manager_user = None
        for manager in candidate:
            if manager.user and manager.user.check_password(sha256(manager_code.encode()).hexdigest()):
                manager_user = manager
                break

        if not manager_user:
            return Response({
                "status": "error",
                "message": "로그인 실패",
                "code": 401,
                "data": [
                    {"detail": "관리자 코드가 올바르지 않습니다."}
                ]
            }, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(manager_user.user)
        data = {
            "status": "success",
            "message": "로그인 성공",
            "code": 200,
            "data": [
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "manager_id": manager_user.id,
                        "manager_name": manager_user.user.user_name,
                        "booth_id": manager_user.booth.booth_id,
                        "operating_status": manager_user.booth.operating_status,
                        "is_restart": manager_user.booth.is_restart
                    }
                }
            ]
        }
        return Response(data, status=status.HTTP_200_OK)
            
    
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

    # 관리자 부스 대기 조회
    @action(detail=False, methods=['get'], url_path='booth')
    def booth_waiting_list(self, request):
        # 로그인 확인
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "인증이 필요합니다.",
                "code": 401,
                "data": [
                    {"detail": "유효한 access 토큰이 필요합니다."}
                ]
            }, status=status.HTTP_401_UNAUTHORIZED)
        # 관리자 여부 확인
        if not request.user.is_manager:
            return custom_response(
                data={'detail': "관리자 유저가 아닙니다."},
                message='권한이 없습니다.',
                code=403,
                success=False
            )

        try:
            booth = request.user.manager_user.booth
            # 취소된 대기는 뒤로 정렬
            queryset = Waiting.objects.filter(booth=booth).annotate(
                canceled_waiting=Case(
                    When(waiting_status__in=['entered'], then=Value(2)),
                    When(waiting_status__in=['canceled', 'time_over'], then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).order_by('canceled_waiting', 'created_at')

            serializer = ManagerWaitingListSerializer(queryset, many=True)
            return custom_response(
                serializer.data, 
                message='관리자 부스 대기 조회 성공',
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)},
                message='관리자 부스 대기 조회 실패',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )

    # 관리자 부스 운영 상태 변경
    @action(detail=False, methods=['post'], url_path='booth/operating-status')
    def change_operating_status(self, request):
        # 로그인 확인
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "인증이 필요합니다.",
                "code": 401,
                "data": [
                    {"detail": "유효한 access 토큰이 필요합니다."}
                ]
            }, status=status.HTTP_401_UNAUTHORIZED)
        # 관리자 여부 확인
        if not request.user.is_manager:
            return custom_response(
                data={'detail': "관리자 유저가 아닙니다."},
                message='권한이 없습니다.',
                code=403,
                success=False
            )
        
        try:
            operating_status = request.data.get('operating_status')
            if operating_status not in ['operating', 'paused']:
                return custom_response(
                    data={'detail': "operating이나 paused로만 변경이 가능합니다."},
                    message='부스 운영 상태 변경 실패',
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    success=False
                )
            
            booth = request.user.manager_user.booth
            if operating_status == booth.operating_status:
                return custom_response(
                    data={'detail': f"이미 {operating_status} 상태입니다."},
                    message='부스 운영 상태 변경 실패',
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    success=False
                )
            
            # 운영 상태 변경
            booth.operating_status = operating_status
            booth.save()

            # is_restart 필드가 False 인 상태에서 운영 상태가 operating으로 변경된다면 is_restart 필드를 True 로 변경
            if booth.is_restart == False and booth.operating_status == 'operating':
                booth.is_restart = True
                booth.save()

            return custom_response(
                data={'operating_status': booth.operating_status},
                message='부스 운영 상태 변경 성공',
                code=status.HTTP_200_OK,
                success=True
            )

        except Exception as e:
            return custom_response(
                data={'detail': str(e)},
                message='부스 운영 상태 변경 실패',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )
        
    @action(detail=False, methods=['get'], url_path='booth/is-restart')
    def get_is_restart(self, request):
        # 로그인 확인
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "인증이 필요합니다.",
                "code": 401,
                "data": [
                    {"detail": "유효한 access 토큰이 필요합니다."}
                ]
            }, status=status.HTTP_401_UNAUTHORIZED)
        # 관리자 여부 확인
        if not request.user.is_manager:
            return custom_response(
                data={'detail': "관리자 유저가 아닙니다."},
                message='권한이 없습니다.',
                code=403,
                success=False
            )
        
        try:
            booth = request.user.manager_user.booth
            is_restart = booth.is_restart

            return custom_response(
                data={
                    'is_restart': is_restart,
                    'operating_status': booth.operating_status
                },
                message='부스 재시작 여부 조회 성공',
                code=status.HTTP_200_OK,
                success=True
            )

        except Exception as e:
            return custom_response(
                data={'detail': str(e)},
                message='부스 재시작 여부 조회 실패',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )

    # 대기중인 대기 조회
    @action(detail=False, methods=['get'], url_path='booth/waiting')
    def get_waiting_waiting(self, request):
        return self.get_booth_queryset(request, ["waiting"])

    # 입장중인 대기 조회
    @action(detail=False, methods=['get'], url_path='booth/entering')
    def get_entering_booth(self, request):
        return self.get_booth_queryset(request, ["entering"])

    # 입장완료 대기 조회
    @action(detail=False, methods=['get'], url_path='booth/entered')
    def get_entered_waiting(self, request):
        return self.get_booth_queryset(request, ["entered"])

    # 입장취소 대기 조회
    @action(detail=False, methods=['get'], url_path='booth/canceled')
    def get_canceled_waiting(self, request):
        return self.get_booth_queryset(request, ["canceled", "time_over"])
        
    # 대기 상태 수 조회
    @action(detail=False, methods=['get'], url_path='booth/status-count')
    def get_waiting_count(self, request):
        # 로그인 확인
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "인증이 필요합니다.",
                "code": 401,
                "data": [
                    {"detail": "유효한 access 토큰이 필요합니다."}
                ]
            }, status=status.HTTP_401_UNAUTHORIZED)
        # 관리자 여부 확인
        if not request.user.is_manager:
            return custom_response(
                data={'detail': "관리자 유저가 아닙니다."},
                message='권한이 없습니다.',
                code=403,
                success=False
            )
        
        try:
            booth = request.user.manager_user.booth
            waiting_team_cnt = Waiting.objects.filter(booth=booth, waiting_status='waiting').count()
            entering_team_cnt = Waiting.objects.filter(booth=booth, waiting_status='entering').count()
            entered_team_cnt = Waiting.objects.filter(booth=booth, waiting_status='entered').count()
            canceled_team_cnt = (Waiting.objects.filter(booth=booth, waiting_status='canceled').count() + 
                                Waiting.objects.filter(booth=booth, waiting_status='time_over').count())
            return custom_response(
                data={
                    'waiting_team_cnt': waiting_team_cnt,
                    'entering_team_cnt': entering_team_cnt,
                    'entered_team_cnt': entered_team_cnt,
                    'canceled_team_cnt': canceled_team_cnt
                },
                message='관리자 부스 대기 조회 성공',
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)},
                message='관리자 부스 대기 조회 실패',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )

# # 부스 웨이팅 조회
# class BoothWaitingViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
#     serializer_class = ManagerWaitingListSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated, IsManagerUser]
#     filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
#     filterset_class = WaitingFilter
#     ordering_fields = ['created_at']  # 대기 생성 시간 순으로 정렬

#     def get_queryset(self):
#         booth = self.request.booth

#         # 취소된 대기는 뒤로 정렬
#         return Waiting.objects.filter(booth=booth).annotate(
#             canceled_waiting=Case(
#                 When(waiting_status__in=['canceled', 'time_over'], then=Value(1)),
#                 default=Value(0),
#                 output_field=IntegerField(),
#             )
#         ).order_by('canceled_waiting', 'created_at')
    
#     @action(detail=True, methods=['post'], url_path='action')
#     def action(self, request, *args, **kwargs):
#         """
#         웨이팅 상태를 변경하는 POST 메서드 (action 기반)
#         request body: {"action": "call", "confirm", "cancel"}
#         """
#         admin = self.request.admin
#         booth = admin.booth

#         # 대기 상태 변경할 대상 가져오기
#         waiting_id = kwargs.get('pk')
#         waiting = get_object_or_404(Waiting, id=waiting_id, booth=booth)

#         # request body에서 action 값을 가져옴
#         action = request.data.get('action', None)

#         if action == 'call':
#             if waiting.waiting_status != 'waiting':
#                 return custom_response(
#                     data=None,
#                     message="Cannot call team while it is not waiting.",
#                     code=status.HTTP_400_BAD_REQUEST,
#                     success=False
#                 )
#             waiting.waiting_status = 'ready_to_confirm'
#             waiting.ready_to_confirm_at = timezone.now()
#             # 문자 메시지 발송
#             phone_number = waiting.user.phone_number
#             sendsms(phone_number, f"[입장확정] 입장 순서가 되어 3분 내로 입장을 확정해 주세요! https://linenow.co.kr")
#             check_ready_to_confirm.apply_async((waiting.id,), countdown=180)  # 3분 후 Task 실행
#         elif action == 'confirm':
#             if waiting.waiting_status != 'confirmed' :
#                 return custom_response(
#                     data=None,
#                     message="Cannot confirm team while it is not confirmed.",
#                     code=status.HTTP_400_BAD_REQUEST,
#                     success=False
#                 )
#             waiting.waiting_status = 'arrived'
#             waiting.confirmed_at = timezone.now()
#         elif action == 'cancel':
#             if waiting.waiting_status in ['canceled', 'time_over_canceled']:
#                 return custom_response(
#                     data=None,
#                     message="This waiting has already been canceled.",
#                     code=status.HTTP_400_BAD_REQUEST,
#                     success=False
#                 )
#             waiting.waiting_status = 'canceled'
#             waiting.canceled_at = timezone.now()
#             # 문자 메시지 발송
#             phone_number = waiting.user.phone_number
#             sendsms(phone_number, f"[대기취소] 부스 사정으로 인해, 대기가 취소되었어요")
#         else:
#             return custom_response(
#                 data=None,
#                 message="Invalid action.",
#                 code=status.HTTP_400_BAD_REQUEST,
#                 success=False
#             )

#         waiting.save()
        
#         serializer = BoothWaitingSerializer(waiting)
#         return custom_response(
#             data=serializer.data,
#             message=f"Waiting status updated to {waiting.waiting_status} successfully!",
#             code=status.HTTP_200_OK
#         )

# # 부스 관리 
# class BoothDetailViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin):
#     # authentication_classes = [JWTAuthentication]
#     # permission_classes = [IsAuthenticated, IsManagerUser]

#     def get_serializer_class(self):
#         if self.action == 'update':
#             return BoothDetailSerializer
#         return BoothSerializer

#     def get_queryset(self):
#         admin = self.request.admin
#         booth = admin.booth

#         return Booth.objects.filter(id=booth.id)
    
#     @action(detail=False, methods=['post'], url_path='status')
#     def update_status(self, request, *args, **kwargs):
#         admin = self.request.admin
#         booth = admin.booth

#         # status 필드가 올바른지 검사, 변수명 충돌을 피하기 위해 _status로 변경
#         _status = request.data.get('status', None)
#         # 부스 정보 업데이트
#         try:
#             serializer = BoothDetailSerializer(booth, data=request.data, partial=True)
#             serializer.is_valid(raise_exception=True)  # raise_exception=True로 유효성 검사를 바로 처리
#             serializer.save()

#             # status가 finished로 변경되면 대기 중인 팀들을 모두 삭제 처리
#             if _status == 'finished':
#                 for waiting in Waiting.objects.filter(booth=booth, waiting_status='waiting'):
#                     waiting.set_canceled()
#                     waiting.save()
#                     # 취소 처리 문자 메시지 발송
#                     phone_number = waiting.user.phone_number
#                     sendsms(phone_number, f"[대기취소] 대기 등록한 부스의 운영이 종료되어, 대기가 취소되었어요")
#                     # 대기 중인 팀들을 모두 삭제 처리
#                     waiting.delete()

#             return custom_response(
#                 data=serializer.data,
#                 message="Booth status updated successfully.",
#                 code=status.HTTP_200_OK
#             )
#         except serializers.ValidationError as e:
#             # 유효성 검사 중 발생한 에러를 400 응답으로 반환
#             return custom_response(
#                 data=e.detail,
#                 message="Validation error.",
#                 code=status.HTTP_400_BAD_REQUEST,
#                 success=False
#             )

#         except Exception as e:
#             # 예상하지 못한 예외 발생 시에도 500 에러 대신 상세한 에러 메시지를 반환
#             return custom_response(
#                 data=str(e),
#                 message="An unexpected error occurred.",
#                 code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 success=False
#             )
        
#     # 부스 대기 상태 변경 endpoint 2개로 분리
#     @action(detail=False, methods=['post'], url_path='pause')
#     def pause(self, request, *args, **kwargs):
#         """
#         부스의 대기 상태를 'paused'로 변경.
#         특정 상태에서는 전환할 수 없음 ('not_started', 'finished', 'paused').
#         """
#         admin = self.request.admin
#         booth = admin.booth

#         # 'not_started', 'finished', 'paused' 상태에서는 'paused'로 전환할 수 없음
#         if booth.is_operated in ['not_started', 'finished', 'paused']:
#             return custom_response(
#                 data=None,
#                 message=f"Cannot pause booth while it is {booth.is_operated}.",
#                 code=status.HTTP_400_BAD_REQUEST,
#                 success=False
#             )

#         # 대기 상태를 'paused'로 변경
#         booth.is_operated = 'paused'
#         booth.save()

#         return custom_response(
#             data={'status': booth.is_operated},
#             message="Booth waiting status changed to paused.",
#             code=status.HTTP_200_OK
#         )
    
#     @action(detail=False, methods=['post'], url_path='resume')
#     def resume(self, request, *args, **kwargs):
#         """
#         부스의 대기 상태를 'operating'으로 변경.
#         특정 상태에서는 전환할 수 없음 ('not_started', 'finished', 'operating').
#         """
#         admin = self.request.admin
#         booth = admin.booth

#         # 'not_started', 'finished', 'operating' 상태에서는 'operating'으로 전환할 수 없음
#         if booth.is_operated in ['not_started', 'finished', 'operating']:
#             return custom_response(
#                 data=None,
#                 message=f"Cannot resume booth while it is {booth.is_operated}.",
#                 code=status.HTTP_400_BAD_REQUEST,
#                 success=False
#             )

#         # 대기 상태를 'operating'으로 변경
#         booth.is_operated = 'operating'
#         booth.save()

#         return custom_response(
#             data={'status': booth.is_operated},
#             message="Booth waiting status changed to operating.",
#             code=status.HTTP_200_OK
#         )

# 상태별 웨이팅 개수 카운트
# class WaitingCountView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated, IsManagerUser]
    
#     def get(self, request):
#         admin = self.request.admin
#         booth = admin.booth

#         waiting_count = WaitingFilter({'status': 'waiting'}, queryset=Waiting.objects.filter(booth=booth)).qs.count()
#         calling_count = WaitingFilter({'status': 'calling'}, queryset=Waiting.objects.filter(booth=booth)).qs.count()
#         arrived_count = WaitingFilter({'status': 'arrived'}, queryset=Waiting.objects.filter(booth=booth)).qs.count()
#         canceled_count = WaitingFilter({'status': 'canceled'}, queryset=Waiting.objects.filter(booth=booth)).qs.count()

#         return custom_response(
#             data={
#                 "waiting": waiting_count,
#                 "calling": calling_count,
#                 "arrived": arrived_count,
#                 "canceled": canceled_count
#             },
#             message="Waiting counts fetched successfully",
#             code=status.HTTP_200_OK
#         )