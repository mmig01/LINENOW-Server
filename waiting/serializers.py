from rest_framework import serializers
from .models import Waiting
from booth.models import Booth
from accounts.models import User
from django.utils import timezone
from datetime import timedelta

# 대기에 사용될 부스 serializer - 부스 모델 수정 후 작성 예정
class WaitingBoothListSerializer(serializers.ModelSerializer):
    booth_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = [
            'booth_id',
            'booth_name',
            'booth_location',
            'booth_thumbnail'
        ]
    
    def get_booth_thumbnail(self, obj):
        request = self.context.get('request')
        thumbnail = obj.booth_images.first()
        if thumbnail and request:
            return request.build_absolute_uri(thumbnail.booth_image.url)
        return ''
    
class WaitingBoothDetailSerializer(serializers.ModelSerializer):
    booth_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = [
            'booth_id',
            'booth_name',
            'booth_location',
            'booth_latitude',
            'booth_longitude',
            'booth_thumbnail'
        ]
    
    def get_booth_thumbnail(self, obj):
        request = self.context.get('request')
        thumbnail = obj.booth_images.first()
        if thumbnail and request:
            return request.build_absolute_uri(thumbnail.booth_image.url)
        return ''

# 대기 리스트 serializer
class WaitingListSerializer(serializers.ModelSerializer):
    waiting_team_ahead = serializers.SerializerMethodField()
    booth_info = serializers.SerializerMethodField()

    class Meta:
        model = Waiting
        fields = [
            'waiting_id',
            'booth_info',
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
    
    def get_booth_info(self, obj):
        request = self.context.get('request')
        return WaitingBoothListSerializer(obj.booth, context={'request': request}).data


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
            'booth_info',
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
    
    def get_booth_info(self, obj):
        request = self.context.get('request')
        return WaitingBoothDetailSerializer(obj.booth, context={'request': request}).data