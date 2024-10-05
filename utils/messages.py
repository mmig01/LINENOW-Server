from rest_framework import status
from utils.responses import custom_response
from django.conf import settings
import requests, re

SSODAA_BASE_URL = settings.SSODAA_BASE_URL
SEND_PHONE = settings.SEND_PHONE

# 문자 발송하기
def sendsms(dest_phone, msg_body):
    # 데이터 형식 검증
    phone_pattern = re.compile(r'^\d{10,11}$')  # 10자리 또는 11자리 숫자만
    if not phone_pattern.match(dest_phone):
        return {
            "message": "Invalid destination phone number.",
        }

    if not isinstance(msg_body, str):
        return {
            "message": "Invalid message content.",
        }
    

    headers = {
        'x-api-key': settings.SMS_API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    }

    data = {
        "token_key": settings.SMS_TOKEN_KEY,
        "msg_type": 'sms',
        "dest_phone": dest_phone,
        "send_phone": SEND_PHONE,
        "msg_body": msg_body,
    }
    print(data)
    return custom_response(data=data, message="perfect", code=status.HTTP_200_OK)
    """
    try:
        url = f"{SSODAA_BASE_URL}/sms/send/sms"
        response = requests.post(url, json=data, headers=headers)
        response = response.json()
        status_code = int(response.get('code'))

        if status_code == 200:
            content = response.get('content')
            data = {
                "sent_messages":content.get('sent_messages'),
                "send_phone":content.get('send_phone'),
            }
            return custom_response(data=data, message=content.get('message'), code=status.HTTP_200_OK)
        
        else:
            error = response.get('error')
            return custom_response(message=error, code=status.HTTP_403_FORBIDDEN, success=False)

    except requests.exceptions.RequestException:
        return custom_response(message="Failed to send messages.", code=status.HTTP_400_BAD_REQUEST, success=False)
    """