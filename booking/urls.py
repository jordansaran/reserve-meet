from django.urls import path, include
from rest_framework.routers import DefaultRouter

from booking.views import RoomViewSet, BookingViewSet, ResourceViewSet, LocationViewSet

booking_router = DefaultRouter()

booking_router.register(r'room', RoomViewSet, basename='room')
booking_router.register(r'booking', BookingViewSet, basename='booking')
booking_router.register(f'resource', ResourceViewSet, basename='resource')
booking_router.register(f'location', LocationViewSet, basename='location')

urlpatterns = [
    path('', include(booking_router.urls)),

]
