from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from .views import *

app_name = 'manager'

faq_router = routers.SimpleRouter()
faq_router.register(r'faqs', FAQViewSet, basename='faqs')


urlpatterns = [
    path('', include(faq_router.urls)),
    
    path('manager/login', AdminLoginView.as_view(), name='admin_login'),
    path('manager/logout', AdminLogoutView.as_view(), name='admin_logout'),
    
    path('manager/waitings', BoothWaitingListView.as_view(), name='booth_waiting_list'),

    path('manager/waitings/status/<str:status_group>', BoothWaitingStatusFilterView.as_view(), name='booth_waiting_status_filter'),

]