# notifications/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Notification
from .serializers import NotificationSerializer
from .permissions import IsRecipient

class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsRecipient]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retourne les notifications de l'utilisateur connecté
        """
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user)
        
        # Filtrer par type de notification
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filtrer par statut de lecture
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            is_read = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Crée une nouvelle notification
        """
        serializer.save(recipient=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Marque une notification comme lue
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        
        return Response({
            'status': 'success',
            'is_read': True
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Marque toutes les notifications de l'utilisateur comme lues
        """
        user = request.user
        count = Notification.objects.filter(recipient=user, is_read=False).count()
        Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
        
        return Response({
            'status': 'success',
            'marked_as_read': count
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Récupère le nombre de notifications non lues
        """
        user = request.user
        count = Notification.objects.filter(recipient=user, is_read=False).count()
        
        return Response({
            'unread_count': count
        })
    
    @action(detail=False, methods=['delete'])
    def delete_all_read(self, request):
        """
        Supprime toutes les notifications lues
        """
        user = request.user
        count = Notification.objects.filter(recipient=user, is_read=True).count()
        Notification.objects.filter(recipient=user, is_read=True).delete()
        
        return Response({
            'status': 'success',
            'deleted': count
        })