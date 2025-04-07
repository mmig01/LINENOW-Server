from rest_framework import serializers
from .models import Booth, Booth_Menu, Booth_Image
from waiting.models import Waiting

class Booth_MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booth_Menu
        fields = ['menu_id', 'menu_name', 'menu_price']

class Booth_ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booth_Image
        fields = ['booth_image_id', 'booth_image']

class BoothListSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = ['booth_id', 'booth_name', 'booth_description', 'booth_location', 'operating_status', 'thumbnail']

    def get_thumbnail(self, obj):
        # 첫 번째 이미지가 썸네일
        
        # 상대 경로 반환
        # thumbnail = obj.Booth_Images.first()
        # if thumbnail:
        #     return thumbnail.image.url
        # return ''
        
        # 절대 경로 반환
        request = self.context.get('request')
        thumbnail = obj.booth_images.first()
        if thumbnail and request:
            return request.build_absolute_uri(thumbnail.booth_image.url)
        return ''
    
class BoothWaitingListSerializer(serializers.ModelSerializer):
    waiting_id = serializers.SerializerMethodField()
    total_waiting_teams = serializers.SerializerMethodField() # 전체 대기 팀
    waiting_status = serializers.SerializerMethodField() # 현재 대기 상태

    class Meta:
        model = Booth
        fields = ['booth_id', 'waiting_id', 'total_waiting_teams', 'waiting_status']

    def get_waiting_id(self, obj):
        print("id")
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-created_at').first()
            return waiting.waiting_id
        return None

    def get_total_waiting_teams(self, obj):
        print("team")
        return Waiting.objects.filter(
            booth=obj, 
            waiting_status__in=['waiting', 'entering']
        ).count()

    # 여러 번 대기를 걸었을 때 가장 최근의 status를 반영
    def get_waiting_status(self, obj):
        print("status")
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-created_at').first()
            if waiting:
                return waiting.waiting_status
        return None

class BoothDetailSerializer(serializers.ModelSerializer):
    menu_info = Booth_MenuSerializer(many=True, source='booth_menus')
    booth_image_info = Booth_ImageSerializer(source='booth_images', many=True)

    class Meta:
        model = Booth
        fields = ['booth_id', 'booth_name', 'booth_description', 'booth_location', 'booth_notice', 'operating_status', 'booth_start_time', 'menu_info', 'booth_image_info']

class BoothWaitingDetailSerializer(serializers.ModelSerializer):
    waiting_id = serializers.SerializerMethodField()
    total_waiting_teams = serializers.SerializerMethodField() # 전체 대기 팀
    waiting_status = serializers.SerializerMethodField() # 현재 대기 상태
    waiting_team_ahead = serializers.SerializerMethodField() # 현재 대기 상태
    confirmed_at = serializers.SerializerMethodField() # 입장 승인 시간

    class Meta:
        model = Booth
        fields = ['booth_id', 'waiting_id', 'total_waiting_teams', 'waiting_status', 'waiting_team_ahead', 'confirmed_at']

    def get_waiting_id(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-created_at').first()
            return waiting.waiting_id
        return None

    def get_total_waiting_teams(self, obj):
        return Waiting.objects.filter(
            booth=obj, 
            waiting_status__in=['waiting', 'entering']
        ).count()

    # 여러 번 대기를 걸었을 때 가장 최근의 status를 반영
    def get_waiting_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-created_at').first()
            if waiting:
                return waiting.waiting_status
        return None

    def get_waiting_team_ahead(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-created_at').first()
            return Waiting.objects.filter(booth=obj, 
                created_at__lt=obj.created_at,
                waiting_status__in=['waiting', 'entering']
            ).count()
        return None

    def get_confirmed_at(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-created_at').first()
            if waiting:
                return waiting.confirmed_at
        return None

class BoothLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booth
        fields = ['booth_id', 'booth_latitude', 'booth_longitude', 'operating_status']