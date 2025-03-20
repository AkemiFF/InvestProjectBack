# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, UserLoginView, EmailVerificationView,
    ResetPasswordRequestView, ResetPasswordConfirmView, UserViewSet,
    InvestorProfileViewSet, ProjectOwnerProfileViewSet, SocialAuthView
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'investor-profiles', InvestorProfileViewSet)
router.register(r'project-owner-profiles', ProjectOwnerProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', UserLoginView.as_view(), name='login'),
    path('auth/verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('auth/reset-password-request/', ResetPasswordRequestView.as_view(), name='reset-password-request'),
    path('auth/reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    path('auth/social/', SocialAuthView.as_view(), name='social-auth'),
]