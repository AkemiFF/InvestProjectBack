# payments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentMethodViewSet, InvoiceViewSet, PaymentProcessViewSet

router = DefaultRouter()
router.register(r'methods', PaymentMethodViewSet, basename='paymentmethod')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'process', PaymentProcessViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]