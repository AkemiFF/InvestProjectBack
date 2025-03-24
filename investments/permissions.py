# investments/permissions.py
from rest_framework import permissions

class IsInvestmentParticipant(permissions.BasePermission):
    """
    Permission pour autoriser uniquement l'investisseur ou le propriétaire du projet à accéder à un investissement
    """
    def has_object_permission(self, request, view, obj):
        # L'investisseur peut toujours accéder à son investissement
        if obj.investor == request.user:
            return True
        
        # Le propriétaire du projet peut accéder aux investissements de son projet
        if obj.project.owner == request.user:
            return True
        
        # Les administrateurs peuvent tout voir
        return request.user.is_staff

class IsTransactionOwner(permissions.BasePermission):
    """
    Permission pour autoriser uniquement le propriétaire d'une transaction à y accéder
    """
    def has_object_permission(self, request, view, obj):
        # L'utilisateur peut accéder à ses propres transactions
        if obj.user == request.user:
            return True
        
        # Les administrateurs peuvent tout voir
        return request.user.is_staff