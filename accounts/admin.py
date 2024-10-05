from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User

class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ('email', 'phone_number', 'nickname', 'is_superuser')
    list_filter = ('is_superuser',)

    # 기본 필드 구성
    fieldsets = (
        (None, {'fields': ('email', 'phone_number', 'nickname', 'password')}),
        ('Permissions', {'fields': ('is_superuser',)}),
    )

    # 유저 생성 시 필드 구성 (슈퍼유저일 때와 일반 유저일 때 다르게)
    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return (
                (None, {'fields': ('email', 'phone_number', 'nickname', 'password1', 'password2')}),
            )
        return (
            (None, {'fields': ('email', 'phone_number', 'nickname')}),
        )

    search_fields = ('email', 'phone_number')
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)
