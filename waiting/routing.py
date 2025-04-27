from django.urls import path

from .consumers import AdminWaitingConsumer, UserWaitingConsumer

websocket_urlpatterns = [
    path("ws/waiting/<int:booth_id>", AdminWaitingConsumer.as_asgi()),
    path("ws/waiting/user", UserWaitingConsumer.as_asgi())
]