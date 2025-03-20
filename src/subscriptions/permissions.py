# subscriptions/permissions.py
from rest_framework import permissions

class IsSubscriptionOwner(permissions.BasePermission):
    """
    Permission pour autoriser uniquement le propriétaire d'un abonnement à y accéder
    """
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur est le propriétaire de l'abonnement
        return obj.user == request.user

class IsProjectBoostOwner(permissions.BasePermission):
    """
    Permission pour autoriser uniquement le propriétaire d'un boost de projet à y accéder
    """
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur est le propriétaire du projet boosté
        return obj.project.owner == request.user