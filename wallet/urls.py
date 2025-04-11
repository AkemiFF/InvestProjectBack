from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'wallets', views.WalletViewSet, basename='wallet')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', views.WalletViewSet.as_view({'post': 'stripe_webhook'}), name='stripe-webhook'),
]
