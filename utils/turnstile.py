import requests
from django.conf import settings
import logging
logger = logging.getLogger(__name__)

def verify_turnstile_token(token):
    """Turnstile 토큰을 Cloudflare에 보내 검증하는 함수"""
    url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
    secret_key = settings.TURNSTILE_SECRET_KEY  # Cloudflare에서 발급받은 비밀키

    data = {
        'secret': secret_key,
        'response': token
    }

    try:
        response = requests.post(url, data=data)
        result = response.json()
        logger.debug(f"Turnstile response: {result}")
        return result.get('success', False)
    except requests.RequestException:
        return False