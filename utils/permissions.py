from rest_framework.permissions import BasePermission
from manager.models import Admin
from .responses import custom_response
from .exceptions import IsNotAdmin

# 어드민 유저
class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        # JWT를 사용해 인증된 사용자 정보 가져오기
        user = request.user
        # 관리자인지 확인
        request.admin = Admin.objects.filter(user=user).first()  # admin 객체를 request에 추가
        if request.admin is None:
            raise IsNotAdmin('The user is not an admin.')
        
        return True

# 일반 유저
class IsUser(BasePermission):
    """
    인증된 사용자만 접근을 허용하는 권한 클래스
    """
    def has_permission(self, request, view):
        # request.user가 인증된 사용자인지 확인
        return bool(request.user and request.user.is_authenticated)