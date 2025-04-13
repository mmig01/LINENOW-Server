from rest_framework import serializers
from .models import User, SMSAuthenticate

class UserSerializer(serializers.ModelSerializer):
    # 프론트엔드에서 입력받는 필드: 패스워드 2개와 sms_code
    user_password1 = serializers.CharField(write_only=True, required=True)
    user_password2 = serializers.CharField(write_only=True, required=True)
    sms_code = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('user_phone', 'user_name', 'no_show_num', 'user_password1', 'user_password2', 'sms_code')
        extra_kwargs = {
            'user_phone': {'required': True},
            'user_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs.get('user_password1') != attrs.get('user_password2'):
            raise serializers.ValidationError({"password": "패스워드가 일치하지 않습니다."})
        return attrs

    def create(self, validated_data):
        # 패스워드와 sms_code는 별도로 처리(예, sms_code는 나중에 검증하는 로직 추가 가능)
        password = validated_data.pop('user_password1')
        validated_data.pop('user_password2')
        validated_data.pop('sms_code', None)  # sms_code 처리 로직 추가 가능
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
class SMSAuthenticateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSAuthenticate
        fields = ['sms_code']