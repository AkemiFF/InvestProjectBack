# users/permissions.py
from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission pour autoriser uniquement le propriétaire ou un admin à accéder à un objet
    """
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur est un admin
        if request.user.is_staff:
            return True
        
        # Vérifier si l'objet a un attribut 'user'
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Sinon, vérifier si l'objet est l'utilisateur lui-même
        return obj == request.user