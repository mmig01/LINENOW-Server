from rest_framework import serializers
from .models import User, SMSAuthenticate

class UserSerializer(serializers.ModelSerializer):
    # 프론트엔드에서 입력받는 필드: 패스워드 2개와 sms_code
    sms_code = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('user_phone', 'user_name', 'sms_code')
        extra_kwargs = {
            'user_phone': {'required': True},
            'user_name': {'required': True},
        }

    def create(self, validated_data):
        validated_data.pop('sms_code', None)  # sms_code 처리 로직 추가 가능
        user = User(**validated_data)
        # None 으로 생성
        user.set_password(None)
        user.save()
        return user
    
class SMSAuthenticateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSAuthenticate
        fields = ['sms_code']

   