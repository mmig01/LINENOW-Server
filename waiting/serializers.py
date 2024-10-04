from rest_framework import serializers
from .models import Waiting
from booth.models import Booth
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# 나의 대기에서 부스 정보 확인용 !! - 아래의 시리얼라이저에서 사용됨 !!
class BoothSerializer(serializers.ModelSerializer):
    booth_id = serializers.IntegerField(source='id')
    thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = Booth
        fields = ['booth_id', 'name', 'description', 'location', 'thumbnail']
    
    def get_thumbnail(self, obj):
        # 부스 첫 번째 이미지가 썸네일로 사용됨
        request = self.context.get('request')
        thumbnail = obj.boothimages.first()
        if thumbnail and request:
            return request.build_absolute_uri(thumbnail.image.url)
        return ''

# 나의 웨이팅 리스트
class WaitingSerializer(serializers.ModelSerializer):
    booth = BoothSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    registered_at = serializers.DateTimeField(read_only=True)
    waiting_teams_ahead = serializers.SerializerMethodField()  # 내 앞에 있는 팀 수를 위한 필드 추가
    confirm_due_time = serializers.SerializerMethodField()  # 3분 더한 시간 반환
    arrival_due_time = serializers.SerializerMethodField()  # 10분 더한 시간 반환

    class Meta:
        model = Waiting
        fields = ['id', 'username', 'booth','party_size', 'waiting_status', 'registered_at', 'ready_to_confirm_at', 'confirmed_at', 'canceled_at', 'waiting_teams_ahead', 'confirm_due_time', 'arrival_due_time']

    def get_waiting_teams_ahead(self, obj):
        return Waiting.objects.filter(
            booth=obj.booth,
            created_at__lt=obj.created_at,
            waiting_status='waiting'
        ).count()
        
    # 3분 더한 시간 반환
    def get_confirm_due_time(self, obj):
        if obj.ready_to_confirm_at:
            return obj.ready_to_confirm_at + timedelta(minutes=3)
        return None

    # 10분 더한 시간 반환
    def get_arrival_due_time(self, obj):
        if obj.confirmed_at:
            return obj.confirmed_at + timedelta(minutes=10)
        return None

# 나의 웨이팅 디테일
class WaitingDetailSerializer(serializers.ModelSerializer):
    booth = BoothSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    registered_at = serializers.DateTimeField(read_only=True)
    waiting_teams_ahead = serializers.SerializerMethodField()
    total_waiting_teams = serializers.SerializerMethodField()
    confirm_due_time = serializers.SerializerMethodField()  # 3분 더한 시간 반환
    arrival_due_time = serializers.SerializerMethodField()  # 10분 더한 시간 반환

    class Meta:
        model = Waiting
        fields = ['id', 'username', 'booth', 'party_size', 'waiting_status', 'registered_at', 'ready_to_confirm_at', 'confirmed_at', 'canceled_at', 'waiting_teams_ahead', 'total_waiting_teams', 'confirm_due_time', 'arrival_due_time']

    def get_waiting_teams_ahead(self, obj):
        return Waiting.objects.filter(
            booth=obj.booth,
            created_at__lt=obj.created_at,
            waiting_status='waiting'
        ).count()
        
    def get_total_waiting_teams(self, obj):
        return Waiting.objects.filter(
            booth=obj.booth,
            waiting_status='waiting'
        ).count()

    # 3분 더한 시간 반환
    def get_confirm_due_time(self, obj):
        if obj.ready_to_confirm_at:
            return obj.ready_to_confirm_at + timedelta(minutes=3)
        return None

    # 10분 더한 시간 반환
    def get_arrival_due_time(self, obj):
        if obj.confirmed_at:
            return obj.confirmed_at + timedelta(minutes=10)
        return None

# 웨이팅 등록 관련 시리얼라이저
class WaitingCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)  # 유저 이름 추가 - 카카오 로그인 연결 후 변경될 듯
    registered_at = serializers.DateTimeField(read_only=True)  # 대기 등록 시간 필드 추가
    booth = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Waiting
        fields = ['id', 'booth', 'username', 'party_size', 'waiting_status', 'registered_at', 'ready_to_confirm_at', 'confirmed_at', 'canceled_at']
        read_only_fields = ['waiting_status', 'registered_at', 'ready_to_confirm_at', 'confirmed_at', 'canceled_at']

    def create(self, validated_data):
        user = self.context['request'].user
        if not isinstance(user, User):
            user = User.objects.get(pk=user.pk)

        validated_data['user'] = user
        return Waiting.objects.create(**validated_data)