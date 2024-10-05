from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'phone_number', 'nickname')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 어드민 외 password 필드 필요없음
        if not self.instance.is_superuser:
            self.fields.pop('password1')
            self.fields.pop('password2')

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'phone_number', 'nickname', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 어드민 외 password 필드 필요없음
        if not self.instance.is_superuser:
            self.fields.pop('password')

class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ('email', 'phone_number', 'nickname', 'is_staff', 'is_superuser')
    list_filter = ('is_superuser',)

    fieldsets = (
        (None, {'fields': ('email', 'phone_number', 'nickname', 'password')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'nickname', 'password1', 'password2') if admin.is_superuser else ('email', 'phone_number', 'nickname'),
        }),
    )
    search_fields = ('email', 'phone_number')
    ordering = ('email',)

admin.site.register(User, UserAdmin)
