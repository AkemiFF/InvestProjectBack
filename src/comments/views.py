# comments/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Comment
from .serializers import (
    CommentSerializer, CommentCreateSerializer, 
    CommentUpdateSerializer, CommentModerationSerializer
)
from .permissions import IsCommentAuthorOrReadOnly, CanModerateComments

class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les commentaires
    """
    queryset = Comment.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsCommentAuthorOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CommentUpdateSerializer
        elif self.action == 'moderate':
            return CommentModerationSerializer
        return CommentSerializer
    
    def get_queryset(self):
        """
        Filtre les commentaires en fonction des paramètres de requête
        """
        queryset = Comment.objects.all()
        
        # Filtrer par projet
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Filtrer par commentaires de premier niveau (sans parent)
        root_only = self.request.query_params.get('root_only')
        if root_only and root_only.lower() == 'true':
            queryset = queryset.filter(parent__isnull=True)
        
        # Filtrer par auteur
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Filtrer par statut d'approbation
        is_approved = self.request.query_params.get('is_approved')
        if is_approved is not None:
            is_approved = is_approved.lower() == 'true'
            queryset = queryset.filter(is_approved=is_approved)
        else:
            # Par défaut, montrer uniquement les commentaires approuvés aux utilisateurs normaux
            if not self.request.user.is_staff:
                # Les utilisateurs peuvent voir leurs propres commentaires non approuvés
                queryset = queryset.filter(
                    Q(is_approved=True) | Q(author=self.request.user)
                )
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Crée un nouveau commentaire
        """
        serializer.save()
    
    def perform_update(self, serializer):
        """
        Met à jour un commentaire existant
        """
        serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[CanModerateComments])
    def moderate(self, request, pk=None):
        """
        Modère un commentaire (approuver/désapprouver)
        """
        comment = self.get_object()
        serializer = self.get_serializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Mettre à jour le statut d'approbation des réponses
        is_approved = serializer.validated_data.get('is_approved')
        if is_approved is not None:
            # Mettre à jour récursivement toutes les réponses
            self._update_replies_approval(comment, is_approved)
        
        return Response(CommentSerializer(comment, context={'request': request}).data)
    
    def _update_replies_approval(self, comment, is_approved):
        """
        Met à jour récursivement le statut d'approbation des réponses
        """
        replies = Comment.objects.filter(parent=comment)
        for reply in replies:
            reply.is_approved = is_approved
            reply.save(update_fields=['is_approved'])
            # Mettre à jour récursivement les réponses de cette réponse
            self._update_replies_approval(reply, is_approved)
    
    @action(detail=False, methods=['get'])
    def my_comments(self, request):
        """
        Liste des commentaires de l'utilisateur connecté
        """
        queryset = Comment.objects.filter(author=request.user)
        
        # Filtrer par projet si spécifié
        project_id = request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CommentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = CommentSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def pending_moderation(self, request):
        """
        Liste des commentaires en attente de modération pour les projets de l'utilisateur
        """
        # Vérifier si l'utilisateur est un porteur de projet
        if not hasattr(request.user, 'project_owner_profile'):
            return Response(
                {"detail": "Vous n'êtes pas un porteur de projet."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer les projets de l'utilisateur
        projects = request.user.projects.all()
        
        # Récupérer les commentaires non approuvés pour ces projets
        queryset = Comment.objects.filter(
            project__in=projects,
            is_approved=False
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CommentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = CommentSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)