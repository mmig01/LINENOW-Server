from rest_framework import serializers
from .models import Booth, BoothMenu, BoothImage
from waiting.models import Waiting
from accounts.models import CustomerUser

class BoothMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoothMenu
        fields = ['menu_id', 'menu_name', 'menu_price']

class BoothImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoothImage
        fields = ['booth_image_id', 'booth_image']

class BoothListSerializer(serializers.ModelSerializer):
    booth_thumbnail = serializers.SerializerMethodField()
    total_waiting_teams = serializers.SerializerMethodField() # 전체 대기 팀

    class Meta:
        model = Booth
        fields = ['booth_id', 'booth_name', 'booth_description', 'booth_location', 'operating_status', 'booth_thumbnail', 'total_waiting_teams']

    def get_booth_thumbnail(self, obj):
        # 상대 경로
        # booth_thumbnail = obj.BoothImages.first()
        # if booth_thumbnail:
        #     return booth_thumbnail.image.url
        # return ''
        
        # 절대 경로
        request = self.context.get('request')
        booth_thumbnail = obj.booth_images.first()
        if booth_thumbnail and request:
            return request.build_absolute_uri(booth_thumbnail.booth_image.url)
        return ''
    
    def get_total_waiting_teams(self, obj):
        return Waiting.objects.filter(
            booth=obj, 
            waiting_status__in=['waiting', 'entering']
        ).count()

class GDGBoothListSerializer(serializers.ModelSerializer):
    booth_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = ['booth_id', 'booth_name', 'booth_description', 'booth_location', 'booth_thumbnail', 'GDG_id']

    def get_booth_thumbnail(self, obj):
        # 상대 경로
        # booth_thumbnail = obj.BoothImages.first()
        # if booth_thumbnail:
        #     return booth_thumbnail.image.url
        # return ''
        
        # 절대 경로
        request = self.context.get('request')
        booth_thumbnail = obj.booth_images.first()
        if booth_thumbnail and request:
            return request.build_absolute_uri(booth_thumbnail.booth_image.url)
        return ''

class BoothWaitingListSerializer(serializers.ModelSerializer):
    waiting_id = serializers.SerializerMethodField()
    waiting_status = serializers.SerializerMethodField() # 현재 대기 상태

    class Meta:
        model = Booth
        fields = ['booth_id', 'waiting_id', 'waiting_status']

    def get_waiting_id(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-created_at').first()
            if waiting:
                return waiting.waiting_id
        return None

    # 여러 번 대기를 걸었을 때 가장 최근의 status를 반영
    def get_waiting_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-created_at').first()
            if waiting:
                return waiting.waiting_status
        return None

class BoothDetailSerializer(serializers.ModelSerializer):
    booth_menu_info = serializers.SerializerMethodField()
    booth_image_info = serializers.SerializerMethodField()
    total_waiting_teams = serializers.SerializerMethodField() # 전체 대기 팀

    class Meta:
        model = Booth
        fields = ['booth_id', 'booth_name', 'booth_description', 'booth_location', 'booth_latitude', 'booth_longitude', 'booth_notice', 'operating_status', 'booth_start_time', 'total_waiting_teams', 'booth_menu_info', 'booth_image_info']

    def get_booth_image_info(self, obj):
        # Return images ordered by booth_image_id ascending
        images = obj.booth_images.all().order_by('booth_image_id')
        serializer = BoothImageSerializer(images, many=True, context=self.context)
        return serializer.data

    def get_booth_menu_info(self, obj):
        menus = obj.booth_menus.all().order_by('menu_id')
        serializer = BoothMenuSerializer(menus, many=True, context=self.context)
        return serializer.data

    def get_total_waiting_teams(self, obj):
        return Waiting.objects.filter(
            booth=obj, 
            waiting_status__in=['waiting', 'entering']
        ).count()

class GDGBoothDetailSerializer(serializers.ModelSerializer):
    booth_image_info = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = ['booth_id', 'booth_name', 'booth_description', 'booth_location', 'booth_notice', 'booth_start_time', 'booth_image_info', 'GDG_id']

    def get_booth_image_info(self, obj):
        images = obj.booth_images.all().order_by('booth_image_id')
        serializer = BoothImageSerializer(images, many=True, context=self.context)
        return serializer.data

class BoothWaitingDetailSerializer(serializers.ModelSerializer):
    waiting_id = serializers.SerializerMethodField()
    waiting_status = serializers.SerializerMethodField() # 현재 대기 상태
    waiting_team_ahead = serializers.SerializerMethodField() # 현재 대기 상태
    confirmed_at = serializers.SerializerMethodField() # 입장 승인 시간
    user_waiting_cnt = serializers.SerializerMethodField() # 대기중인 대기 개수
    user_is_black = serializers.SerializerMethodField() # 대기 요청할 사용자 black list 여부 맞으면 True

    class Meta:
        model = Booth
        fields = ['booth_id', 'waiting_id', 'waiting_status', 'waiting_team_ahead', 'confirmed_at', 'user_waiting_cnt', 'user_is_black']

    def get_waiting_id(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).order_by('-created_at').first()
            if waiting:
                return waiting.waiting_id
        return None

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
            if waiting:
                return Waiting.objects.filter(booth=obj, 
                    created_at__lt=waiting.created_at,
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
    
    def get_user_waiting_cnt(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, waiting_status__in=["waiting", "entering"])
            if waiting:
                return waiting.count()
        return None
    
    def get_user_is_black(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_info = CustomerUser.objects.filter(user=request.user).first()
            if user_info:
                if user_info.no_show_num >= 3:
                    return True
                else:
                    return False
        return None

class BoothLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booth
        fields = ['booth_id', 'booth_latitude', 'booth_longitude', 'operating_status']