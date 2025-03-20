# subscriptions/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionPlanViewSet, SubscriptionViewSet, ProjectBoostViewSet

router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet)
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'boosts', ProjectBoostViewSet, basename='projectboost')

urlpatterns = [
    path('', include(router.urls)),
]