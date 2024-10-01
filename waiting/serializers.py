from rest_framework import serializers
from .models import Waiting
from booth.models import Booth
from django.contrib.auth.models import User

# 나의 대기에서 부스 정보 확인용 !! - 아래의 시리얼라이저에서 사용됨 !!
class BoothSerializer(serializers.ModelSerializer):
    booth_id = serializers.IntegerField(source='id')
    
    class Meta:
        model = Booth
        fields = ['booth_id', 'name', 'description', 'location']

# 나의 웨이팅 리스트
class WaitingSerializer(serializers.ModelSerializer):
    booth = BoothSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    registered_at = serializers.DateTimeField(read_only=True)
    waiting_teams_ahead = serializers.SerializerMethodField()  # 내 앞에 있는 팀 수를 위한 필드 추가

    class Meta:
        model = Waiting
        fields = ['id', 'username', 'booth','party_size', 'waiting_status', 'registered_at', 'ready_to_confirm_at', 'confirmed_at', 'canceled_at', 'waiting_teams_ahead']

    def get_waiting_teams_ahead(self, obj):
        return Waiting.objects.filter(
            booth=obj.booth,
            created_at__lt=obj.created_at,
            waiting_status='waiting'
        ).count()

# 나의 웨이팅 디테일
class WaitingDetailSerializer(serializers.ModelSerializer):
    booth = BoothSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    registered_at = serializers.DateTimeField(read_only=True)
    waiting_teams_ahead = serializers.SerializerMethodField()

    class Meta:
        model = Waiting
        fields = ['id', 'username', 'booth', 'party_size', 'waiting_status', 'registered_at', 'ready_to_confirm_at', 'confirmed_at', 'canceled_at', 'waiting_teams_ahead']

    def get_waiting_teams_ahead(self, obj):
        return Waiting.objects.filter(
            booth=obj.booth,
            created_at__lt=obj.created_at,
            waiting_status='waiting'
        ).count()

# 웨이팅 등록 관련 시리얼라이저
class WaitingCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)  # 유저 이름 추가 - 카카오 로그인 연결 후 변경될 듯
    registered_at = serializers.DateTimeField(read_only=True)  # 대기 등록 시간 필드 추가
    booth = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Waiting
        fields = ['id', 'user', 'booth', 'username', 'party_size', 'waiting_status', 'registered_at', 'ready_to_confirm_at', 'confirmed_at', 'canceled_at']
        read_only_fields = ['waiting_status', 'registered_at', 'ready_to_confirm_at', 'confirmed_at', 'canceled_at']

    def create(self, validated_data):
        user = self.context['request'].user
        if not isinstance(user, User):
            user = User.objects.get(pk=user.pk)

        validated_data['user'] = user
        return Waiting.objects.create(**validated_data)