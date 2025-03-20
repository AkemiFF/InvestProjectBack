# notifications/permissions.py
from rest_framework import permissions

class IsRecipient(permissions.BasePermission):
    """
    Permission pour autoriser uniquement le destinataire d'une notification à y accéder
    """
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur est le destinataire de la notification
        return obj.recipient == request.user