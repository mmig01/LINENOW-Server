import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Case, When, Value, IntegerField, Count, Q
from rest_framework.filters import OrderingFilter
from .models import Booth
from .serializers import BoothListSerializer, BoothDetailSerializer, BoothWaitingListSerializer, BoothWaitingDetailSerializer, BoothLocationSerializer
from rest_framework import viewsets, mixins
from utils.mixins import CustomResponseMixin
from utils.responses import custom_response
from utils.exceptions import *

from rest_framework.views import APIView
import pandas as pd
from rest_framework.parsers import MultiPartParser, FormParser

class BoothViewSet(CustomResponseMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    """
    - GET   /booths                 -> 부스 목록(가나다순)
    - GET   /booths/count           -> 전체 부스 개수
    - GET   /booths/location        -> 부스 위치 목록
    - GET   /booths/{pk}            -> 부스 상세
    """

    def get_serializer_class(self):
        if self.action == 'list':
            return BoothListSerializer 
        return BoothDetailSerializer 
    
    def get_queryset(self):
        # '운영중 - 대기중지 - 운영전 - 운영종료' + 가나다 순서로 정렬
        queryset = Booth.objects.annotate(
            operating_status_order=Case(
                When(operating_status='operating', then=Value(1)),
                When(operating_status='paused', then=Value(2)),
                When(operating_status='not_started', then=Value(3)),
                When(operating_status='finished', then=Value(4)),
                output_field=IntegerField()
            )
        )
        return queryset.order_by('operating_status_order', 'booth_name')

    # 부스 목록 조회
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return custom_response(
                data=serializer.data,
                message='부스 목록 조회 성공',
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)},
                message='부스 목록 조회 실패',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )

    # 전체 부스 개수 조회
    @action(detail=False, methods=['get'], url_path='count')
    def get_booth_count(self, request):
        try:
            booth_count = Booth.objects.count()
            return custom_response(
                {'booth_count': booth_count}, 
                message='전체 부스 개수 조회 성공'
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)}, 
                message='전체 부스 개수 조회 실패', 
                code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                success=False
            )

    #부스 위치 목록 조회
    @action(detail=False, methods=['get'], url_path='location')
    def get_booth_location(self, request):
        try:
            booths = Booth.objects.all()
            serializer = BoothLocationSerializer(booths, many=True)
            return custom_response(
                serializer.data, 
                message='부스 위치 목록 조회 성공',
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)}, 
                message='부스 위치 목록 조회 실패', 
                code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                success=False
            )

    #부스 상세 조회
    def retrieve(self, request, *args, **kwargs):
        try:
            booth = self.get_object()
            serializer = self.get_serializer(booth)
            return custom_response(
                data=serializer.data, 
                message="부스 상세 조회 성공", 
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)}, 
                message='부스 상세 조회 실패', 
                code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                success=False
            )

class BoothWaitingStatusViewSet(CustomResponseMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    """
    - GET   /booths-waiting         -> 부스 목록(가나다순) - 대기 정보
    - GET   /booths-waiting/{pk}    -> 부스 상세 - 대기 정보
    """

    def get_serializer_class(self):
        if self.action == 'list':
            return BoothWaitingListSerializer 
        return BoothWaitingDetailSerializer 
    
    def get_queryset(self):
        # '운영중 - 대기중지 - 운영전 - 운영종료' + 가나다 순서로 정렬
        queryset = Booth.objects.annotate(
            operating_status_order=Case(
                When(operating_status='operating', then=Value(1)),
                When(operating_status='paused', then=Value(2)),
                When(operating_status='not_started', then=Value(3)),
                When(operating_status='finished', then=Value(4)),
                output_field=IntegerField()
            )
        )
        return queryset.order_by('operating_status_order', 'booth_name')
    
    # 부스 목록 - 대기 정보 조회
    def list(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return custom_response(
                data=serializer.data,
                message='부스 대기 목록 조회 성공',
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)},
                message='부스 대기 목록 조회 실패',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )

    # 부스 상세 - 대기 정보 조회
    def retrieve(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response({
                "status": "error",
                "message": "로그인 후 이용해주세요!",
                "code": status.HTTP_401_UNAUTHORIZED,
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        try:
            booth = self.get_object()
            serializer = self.get_serializer(booth)
            return custom_response(
                data=serializer.data, 
                message='부스 대기 상세 조회 성공', 
                code=status.HTTP_200_OK
            )
        except Exception as e:
            return custom_response(
                data={'detail': str(e)}, 
                message='부스 대기 상세 조회 실패', 
                code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                success=False
            )
        
logger = logging.getLogger(__name__)

class BoothDataView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        if not csv_file:
            return custom_response(
                data=None,
                message="파일이 제공되지 않았습니다.",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )
        
        try:
            # CSV 파일을 읽으려고 시도
            df = pd.read_csv(csv_file)
            logger.info("CSV 파일이 성공적으로 로드되었습니다.")
        except Exception as e:
            # 오류 발생 시 로그 출력
            logger.error("CSV 파일 읽기 오류: %s", str(e))
            return custom_response(
                data={'detail': str(e)}, 
                message='csv 파일 읽기를 실패했습니다.', 
                code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                success=False
            )
        
        required_columns = [
            "부스명", "부스 설명", "부스 위치", "운영 시작 시간",
            "운영 마감 시간", "부스 공지", "부스 위치 위도",
            "부스 위치 경도", "부스 운영 상태", "최신 대기 번호"
        ]

        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            logger.error("누락된 열: %s", missing_cols)
            return custom_response(
                data=None,
                message="CSV 파일에 필요한 모든 열이 포함되지 않았습니다.",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False
            )
        
        Booth.objects.all().delete()
        booth_data = []

        for _, row in df.iterrows():
            try:
                booth = Booth.objects.create(
                    booth_name=row["부스명"],
                    booth_description=row["부스 설명"],
                    booth_location=row["부스 위치"],
                    booth_start_time=row["운영 시작 시간"],
                    booth_end_time=row["운영 마감 시간"],
                    booth_notice=row["부스 공지"],
                    booth_latitude=row["부스 위치 위도"],
                    booth_longitude=row["부스 위치 경도"],
                    operating_status=row["부스 운영 상태"],
                    current_waiting_num=row["최신 대기 번호"]
                )
                booth_data.append(booth.booth_name)
            except Exception as e:
                logger.error("부스 생성 오류: %s", str(e))
                return custom_response(
                    data={'detail': str(e)},
                    message="부스 데이터를 저장하는데 실패했습니다.",
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    success=False
                )
        
        return custom_response(
            data={"생성된 부스": booth_data},
            message="부스 데이터가 성공적으로 업로드되었습니다.",
            code=status.HTTP_200_OK,
            success=True
        )