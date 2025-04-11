# payments/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
# router.register(r'methods', PaymentMethodViewSet, basename='paymentmethod')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'process', PaymentProcessViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('create-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('status/<str:payment_id>/', PaymentStatusView.as_view(), name='payment-status'),
    path('session-status/<str:session_id>/', CheckSessionStatusView.as_view(), name='session-status'),
    path('confirm/<str:payment_id>/', ConfirmPaymentView.as_view(), name='confirm-payment'),
    
    # Endpoints pour les méthodes de paiement
    path('methods/', SavedPaymentMethodsView.as_view(), name='payment-methods'),
    path('methods/save/', SavePaymentMethodView.as_view(), name='save-payment-method'),
    path('methods/<str:payment_method_id>/', DeletePaymentMethodView.as_view(), name='delete-payment-method'),
    
    # Webhook Stripe
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]