from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import BookingViewSet, MasterViewSet, ServiceViewSet

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'masters', MasterViewSet, basename='master')
router.register(r'services', ServiceViewSet, basename='service')

urlpatterns = [
    path('', include(router.urls)),
]

