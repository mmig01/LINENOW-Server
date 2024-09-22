from rest_framework.response import Response
from rest_framework import status

def custom_response(data=None, message='Success', code=status.HTTP_200_OK, success=True):
    """
    커스텀 응답 함수
    - data: 실제 응답 데이터
    - message: 응답 메시지
    - code: HTTP 상태 코드
    - status: 성공 여부 (True면 'success', False면 'error')
    """
    response = {
        'status': 'success' if success else 'error',
        'message': message,
        'code': code,
        'data': data if data is not None else None  # 데이터가 없으면 null 반환
    }
    return Response(response, status=code)