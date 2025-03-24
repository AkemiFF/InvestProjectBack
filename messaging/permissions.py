# messaging/permissions.py
from rest_framework import permissions

class IsConversationParticipant(permissions.BasePermission):
    """
    Permission pour autoriser uniquement les participants d'une conversation à y accéder
    """
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur est un participant de la conversation
        return request.user in obj.participants.all()

class IsMessageSenderOrConversationParticipant(permissions.BasePermission):
    """
    Permission pour autoriser l'expéditeur d'un message à le modifier/supprimer
    et les participants de la conversation à le voir
    """
    def has_object_permission(self, request, view, obj):
        # Pour les méthodes de modification, seul l'expéditeur peut modifier son message
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return obj.sender == request.user
        
        # Pour les méthodes de lecture, tous les participants de la conversation peuvent voir le message
        return request.user in obj.conversation.participants.all()