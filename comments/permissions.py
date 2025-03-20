# comments/permissions.py
from rest_framework import permissions

class IsCommentAuthorOrReadOnly(permissions.BasePermission):
    """
    Permission pour autoriser uniquement l'auteur du commentaire à le modifier
    """
    def has_object_permission(self, request, view, obj):
        # Les méthodes GET, HEAD, OPTIONS sont autorisées pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # L'auteur du commentaire peut le modifier
        return obj.author == request.user

class CanModerateComments(permissions.BasePermission):
    """
    Permission pour autoriser la modération des commentaires
    """
    def has_object_permission(self, request, view, obj):
        # L'administrateur peut modérer tous les commentaires
        if request.user.is_staff:
            return True
        
        # Le propriétaire du projet peut modérer les commentaires de son projet
        return obj.project.owner == request.user