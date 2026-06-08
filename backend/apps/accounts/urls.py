from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CaptchaChallengeView,
    CurrentUserView,
    ERPTokenObtainPairView,
    LogoutView,
    PasswordChangeView,
    UserViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("captcha/", CaptchaChallengeView.as_view(), name="captcha-challenge"),
    path("token/", ERPTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("change-password/", PasswordChangeView.as_view(), name="change-password"),
    path("", include(router.urls)),
]
