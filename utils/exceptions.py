from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from .responses import custom_response
'''
    커스텀 예외 처리
    - 커스텀 예외 클래스 정의
    - 커스텀 예외 핸들러 정의
    
    view에서의 사용 방법
    import 예외클래스 from utils.exceptions
    - raise 예외클래스('에러메시지')
'''

# 커스텀 예외 클래스
class ResourceNotFound(APIException):
    status_code = 404
    default_detail = 'The requested resource was not found.'
    default_code = 'resource_not_found'

# 이 아래로 class를 만들어 커스텀 예외를 만들면 됩니다.
# 예시
class CustomException(APIException):
    status_code = 400
    default_detail = 'I hate exceptions :('
    default_code = 'custom_exception' 

#커스텀 토근 오류 클래스
class InvalidToken(APIException):
    status_code = 401
    default_detail = 'The token was invalid.'
    default_code = 'invalid_token' 

# Not Admin
class IsNotAdmin(APIException):
    status_code = 403
    default_detail = 'The user is not an admin.'
    default_code = 'is_not_admin'

# 커스텀 예외 핸들러
def custom_exception_handler(exc, context):
    """
    커스텀 예외 핸들러
    - DRF 기본 핸들러를 확장하여 일관된 에러 응답 제공
    """
    response = exception_handler(exc, context)

    if response is not None:
        message = response.data.get('detail', 'An error occurred.')
        code = response.status_code
        error_type = exc.__class__.__name__  # 에러 타입 가져오기 ..

        return custom_response(data=None, message=f'{error_type}: {message}', code=code, success=False)
    
    return custom_response(data=None, message='Unhandled server error occurred.', code=500, success=False)