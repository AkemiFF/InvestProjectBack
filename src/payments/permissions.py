# payments/permissions.py
from rest_framework import permissions

class IsPaymentMethodOwner(permissions.BasePermission):
    """
    Permission pour autoriser uniquement le propriétaire d'une méthode de paiement à y accéder
    """
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur est le propriétaire de la méthode de paiement
        return obj.user == request.user

class IsInvoiceOwner(permissions.BasePermission):
    """
    Permission pour autoriser uniquement le propriétaire d'une facture à y accéder
    """
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur est le propriétaire de la facture
        return obj.user == request.user