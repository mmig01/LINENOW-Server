from django.urls import path

from .consumers import WaitingConsumer

websocket_urlpatterns = [
    path("ws/waiting/<int:booth_id>", WaitingConsumer.as_asgi()),
]