# users/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'investor-profiles', InvestorProfileViewSet)
router.register(r'project-owner-profiles', ProjectOwnerProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', CustomRefresh.as_view(), name='refresh'),
    path('auth/verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('auth/reset-password-request/', ResetPasswordRequestView.as_view(), name='reset-password-request'),
    path('auth/reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    path('auth/social/', SocialAuthView.as_view(), name='social-auth'),
    path('auth/register/initiate/', initiate_registration, name='initiate_registration'),
    path('auth/register/complete/', complete_registration, name='complete_registration'),
]