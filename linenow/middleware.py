from channels.db import database_sync_to_async
import jwt
from django.conf import settings
from channels.auth import AuthMiddlewareStack
from django.contrib.auth import get_user_model

User = get_user_model()

class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        print("DEBUG: Scope ->", scope)  # 디버깅용 로그
        print("DEBUG: Query String ->", scope.get('query_string', b'').decode())  # 추가 로그

        token = self.get_token_from_scope(scope)
        print("DEBUG: Extracted Token ->", token)  # 토큰 확인

        if token:
            user = await self.authenticate_user(token)
            scope['user'] = user
        return await self.inner(scope, receive, send)

    def get_token_from_scope(self, scope):
        query_string = scope.get('query_string', b'').decode()
        token = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
        return token

    @database_sync_to_async
    def authenticate_user(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            print("DEBUG: JWT Payload ->", payload)  # 추가 로그
            return User.objects.get(id=payload['user_id'])
        except jwt.ExpiredSignatureError:
            print("ERROR: Token has expired")  # 로그 추가
            raise Exception('Token has expired')
        except jwt.DecodeError:
            print("ERROR: Token is invalid")  # 로그 추가
            raise Exception('Token is invalid')
        except User.DoesNotExist:
            print("ERROR: User does not exist")  # 로그 추가
            raise Exception('User does not exist')
