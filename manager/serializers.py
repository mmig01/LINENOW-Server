from .models import FAQ, Admin
from rest_framework import serializers
from waiting.models import Waiting
from django.utils import timezone


# FAQ Serializer
class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'
    

class BoothWaitingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    confirm_remaining_time = serializers.SerializerMethodField()
    arrival_remaining_time = serializers.SerializerMethodField()

    class Meta:
        model = Waiting
        fields = [
            'id', 'user', 'party_size', 'waiting_status', 'ready_to_confirm_at',
            'confirmed_at', 'canceled_at', 'confirm_remaining_time', 'arrival_remaining_time'
        ]

    # 사용자 정보 반환 (이름과 전화번호)
    def get_user(self, obj):
        return {
            # "phone_number": obj.user.phone_number,
            "name": obj.user.username
        }

    # 3분 타이머 필드
    def get_confirm_remaining_time(self, obj):
        if obj.waiting_status == 'ready_to_confirm' and obj.ready_to_confirm_at:
            elapsed_time = (timezone.now() - obj.ready_to_confirm_at).total_seconds()
            minutes, seconds = divmod(max(0, 180 - elapsed_time), 60)
            return f'{int(minutes):02}:{int(seconds):02}'
        return "00:00"

    # 10분 타이머 필드
    def get_arrival_remaining_time(self, obj):
        if obj.waiting_status == 'confirmed' and obj.confirmed_at:
            elapsed_time = (timezone.now() - obj.confirmed_at).total_seconds()
            minutes, seconds = divmod(max(0, 600 - elapsed_time), 60)
            return f'{int(minutes):02}:{int(seconds):02}'
        return "00:00"