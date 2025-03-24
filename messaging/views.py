# messaging/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Max, F, Count
from .models import Conversation, Message
from .serializers import (
    ConversationSerializer, MessageSerializer, ConversationCreateSerializer
)
from .permissions import IsConversationParticipant, IsMessageSenderOrConversationParticipant

class ConversationViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les conversations
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Retourne les conversations de l'utilisateur connecté
        """
        user = self.request.user
        return Conversation.objects.filter(participants=user).annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time')
    
    def get_permissions(self):
        """
        Définit les permissions en fonction de l'action
        """
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'messages', 'mark_as_read']:
            return [permissions.IsAuthenticated(), IsConversationParticipant()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """
        Démarre une nouvelle conversation ou utilise une existante
        """
        serializer = ConversationCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        
        return Response(
            ConversationSerializer(conversation, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Récupère les messages d'une conversation
        """
        conversation = self.get_object()
        messages = conversation.messages.all().order_by('created_at')
        
        # Pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Marque tous les messages non lus d'une conversation comme lus
        """
        conversation = self.get_object()
        unread_messages = conversation.messages.filter(
            is_read=False
        ).exclude(
            sender=request.user
        )
        
        unread_count = unread_messages.count()
        unread_messages.update(is_read=True)
        
        return Response({
            'status': 'success',
            'marked_as_read': unread_count
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Récupère le nombre total de messages non lus pour l'utilisateur
        """
        user = request.user
        count = Message.objects.filter(
            conversation__participants=user,
            is_read=False
        ).exclude(
            sender=user
        ).count()
        
        return Response({
            'unread_count': count
        })

class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les messages
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsMessageSenderOrConversationParticipant]
    
    def get_queryset(self):
        """
        Retourne les messages des conversations de l'utilisateur connecté
        """
        user = self.request.user
        return Message.objects.filter(conversation__participants=user)
    
    def perform_create(self, serializer):
        """
        Crée un nouveau message
        """
        conversation_id = self.request.data.get('conversation')
        conversation = Conversation.objects.get(id=conversation_id)
        
        # Vérifier que l'utilisateur est un participant de la conversation
        if self.request.user not in conversation.participants.all():
            raise permissions.PermissionDenied("Vous n'êtes pas autorisé à envoyer des messages dans cette conversation.")
        
        # Créer le message
        serializer.save(sender=self.request.user, conversation=conversation)
        
        # Mettre à jour la date de la conversation
        conversation.save()  # updated_at sera mis à jour automatiquement
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Marque un message comme lu
        """
        message = self.get_object()
        
        # Vérifier que l'utilisateur n'est pas l'expéditeur du message
        if message.sender == request.user:
            return Response({
                'status': 'error',
                'detail': "Vous ne pouvez pas marquer vos propres messages comme lus."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        message.is_read = True
        message.save(update_fields=['is_read'])
        
        return Response({
            'status': 'success',
            'is_read': True
        })