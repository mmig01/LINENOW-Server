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
        
class ManagerWaitingListSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = Waiting
        fields = ['waiting_id', 'waiting_num', 'person_num', 'waiting_status', 'created_at', 'confirmed_at', 'canceled_at', 'user_info']

    # 사용자 정보 반환 (이름과 전화번호)
    def get_user_info(self, obj):
        return {
            "user_name": obj.user.user_name,
            "user_phone": obj.user.user_phone
        }
    
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