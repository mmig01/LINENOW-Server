"""
ASGI config for linenow project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linenow.settings')

application = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
import waiting.routing
from linenow.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": application,
    "websocket": AuthMiddlewareStack(
        JWTAuthMiddleware(
            AllowedHostsOriginValidator(
            URLRouter(
                waiting.routing.websocket_urlpatterns
            )     
            ),
        ),
    ),
})
