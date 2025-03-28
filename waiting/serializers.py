from rest_framework import serializers
from .models import Waiting
from booth.models import Booth
from accounts.models import User
from django.utils import timezone
from datetime import timedelta

# 대기에 사용될 부스 serializer - 부스 모델 수정 후 작성 예정

# 대기 리스트 serializer
class WaitingListSerializer(serializers.ModelSerializer):
    waiting_team_ahead = serializers.SerializerMethodField()

    class Meta:
        model = Waiting
        fields = [
            'waiting_id',
            # 'booth_info',
            'waiting_team_ahead',
            'waiting_status',
            'created_at',
            'confirmed_at',
            'canceled_at',
        ]

    def get_waiting_team_ahead(self, obj):
        return Waiting.objects.filter(
            booth=obj.booth,
            created_at__lt=obj.created_at,
            waiting_status='waiting'
        ).count()


class WaitingDetailSerializer(serializers.ModelSerializer):
    waiting_team_ahead = serializers.SerializerMethodField()

    class Meta:
        model = Waiting
        fields = [
            'waiting_id',
            'waiting_num',
            'person_num',
            'waiting_team_ahead',
            'waiting_status',
            # 'booth_info',
            'created_at',
            'confirmed_at',
            'canceled_at'
        ]
    
    def get_waiting_team_ahead(self, obj):
        return Waiting.objects.filter(
            booth=obj.booth,
            created_at__lt=obj.created_at,
            waiting_status='waiting'
        ).count()