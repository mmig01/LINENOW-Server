from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from .views import FAQViewSet

app_name = 'manager'

faq_router = routers.SimpleRouter()
faq_router.register(r'faqs', FAQViewSet, basename='faqs')


urlpatterns = [
    path('', include(faq_router.urls)),

]