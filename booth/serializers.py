from rest_framework import serializers
from .models import Booth, BoothMenu, BoothImage
from waiting.models import Waiting

class BoothMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoothMenu
        fields = ['name', 'price']

# 부스 리스트
class BoothListSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    # 사용자 대기 관련
    is_waiting = serializers.SerializerMethodField()
    waiting_status = serializers.SerializerMethodField()
    # 대기 팀 수 관련
    total_waiting_teams = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = ['id', 'name', 'description', 'location', 'is_operated', 'thumbnail', 'total_waiting_teams', 'is_waiting', 'waiting_status']

    def get_thumbnail(self, obj):
        # 첫 번째 이미지가 썸네일 ! !
        
        # 상대 경로 반환
        # thumbnail = obj.boothimages.first()
        # if thumbnail:
        #     return thumbnail.image.url
        # return ''
        
        # 절대 경로 반환
        request = self.context.get('request')
        thumbnail = obj.boothimages.first()
        if thumbnail and request:
            return request.build_absolute_uri(thumbnail.image.url)
        return ''
    
    def get_total_waiting_teams(self, obj):
        return Waiting.objects.filter(
            booth=obj, 
            waiting_status__in=['waiting', 'ready_to_confirm', 'confirmed']
        ).count()

    # 사용자 대기 관련 
    def get_is_waiting(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Waiting.objects.filter(
                user=request.user, 
                booth=obj,
                waiting_status__in=['waiting', 'ready_to_confirm', 'confirmed']
            ).exists()
        return False

    # 여러 번 대기를 걸었을 때 가장 최근의 status를 반영
    def get_waiting_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-registered_at').first()
            if waiting:
                return waiting.waiting_status
        return None
    
class BoothImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoothImage
        fields = ['image']

# 부스 디테일
class BoothDetailSerializer(serializers.ModelSerializer):
    menu = BoothMenuSerializer(many=True, source='menus')
    images = BoothImageSerializer(source='boothimages', many=True)
    # 사용자 대기 관련
    is_waiting = serializers.SerializerMethodField()
    waiting_status = serializers.SerializerMethodField()
    waiting_id = serializers.SerializerMethodField()
    # 대기 팀 수 관련
    waiting_teams_ahead = serializers.SerializerMethodField()
    total_waiting_teams = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = ['id', 'name', 'description', 'location', 'caution', 'is_operated', 'images', 'menu', 'open_time', 'close_time', 'total_waiting_teams', 'waiting_teams_ahead', 'is_waiting', 'waiting_id', 'waiting_status']

    # 대기 팀 수 관련
    def get_waiting_teams_ahead(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            current_waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-registered_at').first()
            if current_waiting:
                # 현재 유저의 등록 시점보다 이전에 등록한 사람들 (waiting, ready_to_confirm, confirmed 상태만 체크)
                return Waiting.objects.filter(
                    booth=obj,
                    waiting_status__in=['waiting', 'ready_to_confirm', 'confirmed'],
                    registered_at__lt=current_waiting.registered_at
                ).count()
        return 0
    
    def get_total_waiting_teams(self, obj):
        return Waiting.objects.filter(
            booth=obj, 
            waiting_status__in=['waiting', 'ready_to_confirm', 'confirmed']
        ).count()
    
    # 사용자 대기 관련 
    def get_is_waiting(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Waiting.objects.filter(
                user=request.user, 
                booth=obj,
                waiting_status__in=['waiting', 'ready_to_confirm', 'confirmed']
            ).exists()
        return False

    def get_waiting_id(self, obj):
        request = self.context.get('request')
        # is_waiting=true일 때만 waiting_id를 반환
        if self.get_is_waiting(obj):
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-registered_at').first()
            if waiting:
                return waiting.id
        return None

    def get_waiting_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-registered_at').first()
            if waiting:
                return waiting.waiting_status
        return None
