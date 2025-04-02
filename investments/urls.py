# investments/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InvestmentViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'', InvestmentViewSet, basename='investment')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]