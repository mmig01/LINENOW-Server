from datetime import timezone
from rest_framework.response import Response
from rest_framework import mixins, viewsets
from .models import *
from .serializers import *

from rest_framework import status
from django.shortcuts import get_object_or_404

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
    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        serializer = ManagerSerializer(data=request.data)
        if serializer.is_valid():
            try:
                manager = serializer.save()
                # refresh = RefreshToken.for_user(manager)  # Manager가 BaseUser여야 합니다.
                # access  = refresh.access_token
            except Exception as e:
                return Response({
                    "status": "error",
                    "message": "로그인 실패",
                    "code": 500,
                    "data": [
                    str(e)
                    ]
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

            return Response({
            "status": "success",
            "message": "매니저 회원가입 성공",
            "code": 200,
            "data": [
                {
                    # "access": str(access),
                    # "refresh": str(refresh),
                    "manager": {
                        "manager_id": manager.manager_id,
                        "booth": manager.booth.booth_name,
                    }
                }
            ]
        }, status=status.HTTP_200_OK)
        else:
            error = {}
            for field, error_list in serializer.errors.items():
                for error in error_list:
                    # error는 ErrorDetail 객체입니다.
                    error = {"detail": f"{field}: {error}"}
            return Response({
                "status": "error",
                "message": "로그인 실패",
                "code": 500,
                "data": [
                   error
                ]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = ManagerSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['manager_code']

            # 1) manager_code를 기준으로 Manager 객체 조회
            manager = get_object_or_404(Manager, manager_code=sha256(code.encode('utf-8')).hexdigest())

            # 2) (선택) 해시 비교가 필요하다면 check_password() 로 검증
            #    만약 plain-text로 저장했다면 위 단계만으로 충분합니다.
            # if not check_password(code, manager.manager_code):
            #     return Response(..., status=status.HTTP_401_UNAUTHORIZED)

            # 3) 토큰 발급 (여기선 Manager 모델 인스턴스를 user처럼 간주)
            refresh = RefreshToken.for_user(manager)  # Manager가 BaseUser여야 합니다.
            access  = refresh.access_token

            return Response({
            "status": "success",
            "message": "매니저 로그인 성공",
            "code": 200,
            "data": [
                {
                    "access": str(access),
                    "refresh": str(refresh),
                    "manager": {
                        "manager_id": manager.manager_id,
                        "booth": manager.booth.booth_name,
                    }
                }
            ]
        }, status=status.HTTP_200_OK)
        else:
            error = {}
            for field, error_list in serializer.errors.items():
                for error in error_list:
                    # error는 ErrorDetail 객체입니다.
                    error = {"detail": f"{field}: {error}"}
            return Response({
                "status": "error",
                "message": "로그인 실패",
                "code": 500,
                "data": [
                   error
                ]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# # 부스 웨이팅 조회
# class BoothWaitingViewSet(CustomResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated, IsManagerUser]
#     serializer_class = BoothWaitingSerializer
#     filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
#     filterset_class = WaitingFilter
#     ordering_fields = ['created_at']  # 대기 생성 시간 순으로 정렬

#     def get_queryset(self):
#         admin = self.request.admin
#         booth = admin.booth

#         # 해당 부스의 대기 목록 반환
#         return Waiting.objects.filter(booth=booth).annotate(
#         canceled_order=Case(
#             When(waiting_status__in=['canceled', 'time_over_canceled'], then=Value(1)),
#             default=Value(0),
#             output_field=IntegerField(),
#         )
#     ).order_by('canceled_order', 'registered_at')  # 취소된 순서대로 뒤로 정렬
    
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
# class BoothDetailViewSet(CustomResponseMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated, IsManagerUser]

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

# # 상태별 웨이팅 개수 카운트
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