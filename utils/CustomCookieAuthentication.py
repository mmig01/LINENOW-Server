from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CustomCookieAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # 쿠키에서 access_token 가져오기
        access_token = request.COOKIES.get('access_token')

        if access_token is None:
            return None  # 토큰이 없으면 인증 실패

        try:
            # JWT 토큰 유효성 검사 및 사용자 인증 처리
            validated_token = self.get_validated_token(access_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except AuthenticationFailed as e:
            raise AuthenticationFailed('Token is invalid or expired')