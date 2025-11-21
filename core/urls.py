from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from core.views import (
    CustomTokenObtainPairView,
    UserViewSet,
    UserSessionViewSet,
    LogoutView,
    LogoutAllView,
)


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'sessions', UserSessionViewSet, basename='session')

urlpatterns = [
    # JWT Authentication
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Logout
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/logout-all/', LogoutAllView.as_view(), name='logout_all'),

    # User and Session endpoints
    path('api/', include(router.urls)),
]
