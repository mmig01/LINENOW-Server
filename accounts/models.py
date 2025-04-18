from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, user_phone, password=None, **extra_fields):
        if not user_phone:
            raise ValueError(_("The phone number must be set"))
        if 'user_name' not in extra_fields or not extra_fields['user_name']:
            raise ValueError(_("The user name must be set"))
        user = self.model(user_phone=user_phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("user_name", user_phone)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(user_phone, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    user_phone = models.CharField(
        max_length=20,
        unique=True,
        help_text=_("User phone number, used for authentication.")
    )
    user_name = models.CharField(
        max_length=10,
        help_text=_("Name of the user.")
    )
    no_show_num = models.IntegerField(default=0)
    # Dummy email 필드를 추가 (이메일 기능은 사용하지 않으므로, blank와 null 허용)
    email = models.EmailField(blank=True, null=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'user_phone'
    REQUIRED_FIELDS = ['user_name']

    def __str__(self):
        return self.user_phone
    
from django.db import models
from django.utils import timezone

class SMSAuthenticate(models.Model):
    user_phone = models.CharField(max_length=20, help_text="인증 받을 전화번호")
    sms_code = models.TextField(help_text="문자인증 코드")
    created_at = models.DateTimeField(auto_now_add=True, help_text="인증 코드 발송 시각")

    def __str__(self):
        return f"{self.user_phone} - {self.sms_code}"

    def is_expired(self):
        """
        인증 코드의 유효기간을 체크합니다. (예: 1분)
        """
        now = timezone.now()
        expiration_time = self.created_at + timezone.timedelta(minutes=1)
        return now > expiration_time