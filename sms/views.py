from rest_framework import status
from rest_framework.decorators import api_view
from utils.responses import custom_response
from django.conf import settings
import requests

SSODAA_BASE_URL = settings.SSODAA_BASE_URL

# 문자 발송하기
@api_view(['POST'])
def sendsms(request):
    dest_phone = request.data.get('dest_phone')
    msg_body = request.data.get('msg_body')
    send_phone = settings.SEND_PHONE

    headers = {
        'x-api-key': settings.SMS_API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    }

    data = {
        "token_key": settings.SMS_TOKEN_KEY,
        "msg_type": 'sms',
        "dest_phone": dest_phone,
        "send_phone": send_phone,
        "msg_body": msg_body,
    }
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
        