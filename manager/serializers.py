from hashlib import sha256

from accounts.models import User
from .models import Ask, Manager
from booth.models import Booth
from rest_framework import serializers
from waiting.models import Waiting
from datetime import timedelta


# Ask Serializer
class AskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ask
        fields = '__all__'
    
class ManagerSerializer(serializers.ModelSerializer):
    manager_code = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ('user_phone', 'user_name', 'manager_code')
        extra_kwargs = {
            'user_phone': {'required': True},
            'user_name': {'required': True},
            'manager_code': {'required': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('manager_code')
        hashed_password = sha256(password.encode()).hexdigest()
        user = User(**validated_data)
        user.set_password(hashed_password)
        user.save()
        return user
        
class BoothWaitingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    confirm_due_time = serializers.SerializerMethodField()  # 3분 더한 시간 반환
    arrival_due_time = serializers.SerializerMethodField()  # 10분 더한 시간 반환

    class Meta:
        model = Waiting
        fields = [
            'id', 'user', 'party_size', 'waiting_status', 'registered_at','ready_to_confirm_at',
            'confirmed_at', 'canceled_at', 'confirm_due_time', 'arrival_due_time'
        ]

    # 사용자 정보 반환 (이름과 전화번호)
    def get_user(self, obj):
        return {
            "phone_number": obj.user.phone_number,
            "name": obj.user.name
        }

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
    
class BoothDetailSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='is_operated')
    
    def validate_status(self, value):
        # 'status' 필드의 값이 올바른지 검사
        if value not in dict(Booth.OPERATED_STATUS).keys():
            raise serializers.ValidationError(f"Invalid value for status. Expected one of {list(dict(Booth.OPERATED_STATUS).keys())}.")
        return value

    class Meta:
        model = Booth
        fields = ['id', 'name', 'status']

class BoothSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='is_operated')

    class Meta:
        model = Booth
        # fields = '__all__'
        # 필드 제거
        exclude = ['is_operated']