from rest_framework import mixins, viewsets
from rest_framework.response import Response
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from utils.responses import custom_response

# FAQ 리스트 조회만 가능한 ViewSet
class FAQViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    
    
# 관리자 로그인 로그아웃
class AdminLoginView(APIView):
    def post(self, request):
        admin_code = request.data.get('admin_code')
        
        try:
            admin = Admin.objects.get(admin_code=admin_code)
        except Admin.DoesNotExist:
            # 고유번호가 틀렸을 때
            return custom_response(data=None, message="Invalid admin code. Please check and try again.", code=status.HTTP_400_BAD_REQUEST, success=False)
        
        # 로그인 처리 (세션 or 토큰 저장 등)
        request.session['admin_id'] = admin.id  # 세션에 관리자 ID 저장
        
        booth_name = admin.booth.name if admin.booth else "No booth assigned"
        return custom_response(data={'booth_name': booth_name}, message=f"Login Success !!! Hi, {booth_name} manager.", code=status.HTTP_200_OK)

class AdminLogoutView(APIView):
    def post(self, request):
        admin_id = request.session.get('admin_id')
        
        if admin_id:
            # 세션에서 admin_id를 이용해 관리자 정보를 가져옴
            admin = get_object_or_404(Admin, id=admin_id)
            booth_name = admin.booth.name if admin.booth else "No booth assigned"
            
            # 세션 삭제로 로그아웃 처리
            request.session.flush()
            
            return custom_response(data={'booth_name': booth_name}, message=f"Successfully logged out from {booth_name}.", code=status.HTTP_200_OK)
        
        return custom_response(data=None, message="No active session found to log out.", code=status.HTTP_400_BAD_REQUEST, success=False)
    
class BoothWaitingListView(APIView):
    def get(self, request, boothid):
        admin_id = request.session.get('admin_id')  # 세션에서 관리자 ID 가져오기
        
        if not admin_id:
            return custom_response(data=None, message="You must be logged in as an admin to view reservations.", code=status.HTTP_403_FORBIDDEN, success=False)
        
        admin = get_object_or_404(Admin, id=admin_id)  # 로그인한 관리자 정보
        booth = get_object_or_404(Booth, id=boothid)  # 요청된 부스 정보
        
        # 관리자가 해당 부스를 관리하는지 확인
        if admin.booth.id != booth.id:
            return custom_response(data=None, message="You do not have permission to view this booth's reservations.", code=status.HTTP_403_FORBIDDEN, success=False)
        
        # 해당 부스의 모든 대기 정보 조회
        waitings = Waiting.objects.filter(booth=booth).order_by('created_at')  # 대기 생성 시간 순으로 정렬
        serializer = BoothWaitingSerializer(waitings, many=True)
        
        return custom_response(data=serializer.data, message="Booth waiting status fetched successfully", code=status.HTTP_200_OK)
    
# 웨이팅 상태별 필터링
class BoothWaitingStatusFilterView(APIView):
    def get(self, request, boothid, status_group):
        admin_id = request.session.get('admin_id')  # 세션에서 관리자 ID 가져오기
        
        if not admin_id:
            return custom_response(data=None, message="You must be logged in as an admin to view reservations.", code=status.HTTP_403_FORBIDDEN, success=False)
        
        admin = get_object_or_404(Admin, id=admin_id)  # 로그인한 관리자 정보
        booth = get_object_or_404(Booth, id=boothid)  # 요청된 부스 정보
        
        # 관리자가 해당 부스를 관리하는지 확인
        if admin.booth.id != booth.id:
            return custom_response(data=None, message="You do not have permission to view this booth's reservations.", code=status.HTTP_403_FORBIDDEN, success=False)
        
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