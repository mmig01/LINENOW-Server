from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'phone_number', 'nickname')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.is_superuser:
            # 일반 유저는 비밀번호 입력 필드를 제외
            self.fields.pop('password1')
            self.fields.pop('password2')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'phone_number', 'nickname', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.is_superuser:
            # 일반 유저는 비밀번호 필드를 제외
            self.fields.pop('password')
