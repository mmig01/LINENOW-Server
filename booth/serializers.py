from rest_framework import serializers
from .models import Booth, BoothMenu, BoothImage
from waiting.models import Waiting

class BoothMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoothMenu
        fields = ['name', 'price']
        
    def get_price(self, obj):
        return f'{int(obj.price):,}원'

class BoothListSerializer(serializers.ModelSerializer):
    menu = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    waiting_count = serializers.SerializerMethodField()
    # 사용자 대기 관련
    is_waiting = serializers.SerializerMethodField()
    waiting_status = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = ['id', 'name', 'description', 'location', 'is_operated', 'thumbnail', 'menu', 'open_time', 'close_time', 'waiting_count', 'is_waiting', 'waiting_status']

    def get_menu(self, obj):
        menus = obj.menus.all()
        if menus:
            return [f'{menu.name}: {int(menu.price):,}원' for menu in menus]
        return []

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

    # 사용자 대기 관련 
    def get_is_waiting(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Waiting.objects.filter(user=request.user, booth=obj).exists()
        return False

    def get_waiting_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).first()
            if waiting:
                return waiting.waiting_status
        return None
    
    def get_waiting_count(self, obj):
        return obj.waitings.count()
    
class BoothImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoothImage
        fields = ['image']

class BoothDetailSerializer(serializers.ModelSerializer):
    menu = serializers.SerializerMethodField()
    images = BoothImageSerializer(source='boothimages', many=True)
    waiting_count = serializers.SerializerMethodField()
    # 사용자 대기 관련
    is_waiting = serializers.SerializerMethodField()
    waiting_status = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = ['id', 'name', 'description', 'location', 'is_operated', 'images', 'menu', 'open_time', 'close_time', 'waiting_count', 'is_waiting', 'waiting_status']

    def get_menu(self, obj):
        menus = obj.menus.all()
        if menus:
            return [f'{menu.name}: {int(menu.price):,}원' for menu in menus]
        return []

    # 사용자 대기 관련
    def get_is_waiting(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Waiting.objects.filter(user=request.user, booth=obj).exists()
        return False

    def get_waiting_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            waiting = Waiting.objects.filter(user=request.user, booth=obj).first()
            if waiting:
                return waiting.waiting_status
        return None
    
    def get_waiting_count(self, obj):
        return obj.waitings.count()