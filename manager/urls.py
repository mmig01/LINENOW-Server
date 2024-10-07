from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from .views import *

app_name = 'manager'

faq_router = routers.SimpleRouter(trailing_slash=False)
faq_router.register(r'faqs', FAQViewSet, basename='faqs')

booth_waiting_router = routers.SimpleRouter(trailing_slash=False)
booth_waiting_router.register(r'waitings', BoothWaitingViewSet, basename='waitings')

booth_detail_router = routers.SimpleRouter(trailing_slash=False)
booth_detail_router.register(r'booth', BoothDetailViewSet, basename='booth')

urlpatterns = [
    path('', include(faq_router.urls)),
    path('manager/', include(booth_waiting_router.urls)),
    path('manager/', include(booth_detail_router.urls)),
    path('manager/login', AdminLoginView.as_view(), name='admin_login'),
    path('manager/logout', AdminLogoutView.as_view(), name='admin_logout'),
    path('manager/waiting-counts', WaitingCountView.as_view(), name='waiting_counts'),
    # path('manager/waitings', BoothWaitingListView.as_view(), name='booth_waiting_list'),
    # path('manager/waitings/status/<str:status_group>', BoothWaitingStatusFilterView.as_view(), name='booth_waiting_status_filter'),

]