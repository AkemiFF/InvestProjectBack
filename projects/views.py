# projects/views.py
import json
import os
from django.http import FileResponse

from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import ProjectFilter
from .models import Project, ProjectMedia, Sector
from .serializers import *


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission pour autoriser uniquement les propriétaires à modifier un projet
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user

class SectorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les secteurs d'activité
    """
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les projets
    """
    queryset = Project.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ProjectFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'amount_raised', 'deadline', 'participants_count']
    ordering = ['-created_at']
    
    def create(self, request, *args, **kwargs):
        data = request.data
        data['owner'] = request.user.id  # Assigner l'utilisateur connecté comme propriétaire
        print(data)
        # Sérialisation et validation des données du projet
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            print("Erreurs de validation :", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Création du projet principal
        project = serializer.save()

        # Gestion des fichiers (images et documents)
        cover_image = request.FILES.get('cover_image')
        if cover_image:
            ProjectMedia.objects.create(
                project=project,
                file=cover_image,
                file_type='image', 
                cover=True  
            )
        # Gestion des membres de l'équipe
        teams = data.get('team', [])
        try:
            teams = json.loads(data.get('team', '[]'))
        except json.JSONDecodeError:
            return Response(
                {"detail": "Le format de l'équipe est invalide."},
                status=status.HTTP_400_BAD_REQUEST
            )
        print(teams)
        for team in teams:
            print(team)
            TeamMember.objects.create(
            project=project,
            name=team.get('name'),
            role=team.get('role'),
            photo=team.get('photo'),
            facebook_url=team.get('facebook_url')
            )
            
        images = request.FILES.getlist('images')
        for image in images:
            ProjectMedia.objects.create(
                project=project,
                file=image,
                file_type='image'
            )

        documents = request.FILES.getlist('documents')
        for document in documents:
            ProjectMedia.objects.create(
                project=project,
                file=document,
                title=document.name,
                file_type='doc'
            )

        # Retourner la réponse avec les données du projet créé
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action in [ 'update', 'partial_update']:
            return ProjectCreateUpdateSerializer
        elif self.action in ['create']:
            return ProjectCreateSerializer
        return ProjectDetailSerializer
    
    def get_queryset(self):
        queryset = Project.objects.all()
        
        # Filtrer par statut actif par défaut pour les listes publiques
        if self.action == 'list' and not self.request.query_params.get('status'):
            queryset = queryset.filter(status='active')
        
        # Filtrer par projets en vedette
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Filtrer par projets qui se terminent bientôt
        ending_soon = self.request.query_params.get('ending_soon')
        if ending_soon and ending_soon.lower() == 'true':
            import datetime

            from django.utils import timezone
            seven_days_later = timezone.now().date() + datetime.timedelta(days=7)
            queryset = queryset.filter(deadline__lte=seven_days_later, deadline__gte=timezone.now().date())
        
        # Filtrer par nouveaux projets
        new = self.request.query_params.get('new')
        if new and new.lower() == 'true':
            import datetime

            from django.utils import timezone

            thirty_days_ago = timezone.now().date() - datetime.timedelta(days=30)
            queryset = queryset.filter(created_at__gte=thirty_days_ago)
        
        # Filtrer par projets favoris de l'utilisateur
        favorites = self.request.query_params.get('favorites')
        if favorites and favorites.lower() == 'true' and self.request.user.is_authenticated:
            queryset = self.request.user.favorite_projects.all()
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Incrémenter le compteur de vues
        instance.views_count = F('views_count') + 1
        instance.save(update_fields=['views_count'])
        instance.refresh_from_db()  # Recharger pour obtenir la valeur mise à jour
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def add_media(self, request, pk=None):
        project = self.get_object()
        
        # Vérifier que l'utilisateur est le propriétaire du projet
        if project.owner != request.user:
            return Response(
                {"detail": "Vous n'êtes pas autorisé à ajouter des médias à ce projet."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProjectMediaCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['delete'])
    def remove_media(self, request, pk=None):
        project = self.get_object()
        
        # Vérifier que l'utilisateur est le propriétaire du projet
        if project.owner != request.user:
            return Response(
                {"detail": "Vous n'êtes pas autorisé à supprimer des médias de ce projet."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        media_id = request.data.get('media_id')
        if not media_id:
            return Response(
                {"detail": "L'ID du média est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            media = ProjectMedia.objects.get(id=media_id, project=project)
            media.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProjectMedia.DoesNotExist:
            return Response(
                {"detail": "Média non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        project = self.get_object()
        user = request.user
        
        if user.favorite_projects.filter(id=project.id).exists():
            user.favorite_projects.remove(project)
            return Response({"status": "removed from favorites"})
        else:
            user.favorite_projects.add(project)
            return Response({"status": "added to favorites"})
    
    @action(detail=False, methods=['get'])
    def my_projects(self, request):
        """
        Liste des projets de l'utilisateur connecté
        """
        queryset = Project.objects.filter(owner=request.user)
        
        # Filtrer par statut si spécifié
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProjectListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProjectListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, pk=None):
        """
        Soumettre un projet pour validation
        """
        project = self.get_object()
        
        # Vérifier que l'utilisateur est le propriétaire du projet
        if project.owner != request.user:
            return Response(
                {"detail": "Vous n'êtes pas autorisé à soumettre ce projet."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que le projet est en brouillon
        if project.status != 'draft':
            return Response(
                {"detail": "Seuls les projets en brouillon peuvent être soumis pour validation."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        project.status = 'pending'
        project.save(update_fields=['status'])
        
        return Response({"status": "Le projet a été soumis pour validation."})

    @action(detail=True, methods=['post'])
    def add_team_member(self, request, pk=None):
        """
        Ajouter un membre à l'équipe du projet
        """
        project = self.get_object()
            
        # Vérifier que l'utilisateur est le propriétaire du projet
        if project.owner != request.user:
            return Response(
                {"detail": "Vous n'êtes pas autorisé à ajouter des membres à l'équipe de ce projet."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = ProjectTeamMemberSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_team_member(self, request, pk=None):
        """
        Supprimer un membre de l'équipe du projet
        """
        project = self.get_object()
        
        # Vérifier que l'utilisateur est le propriétaire du projet
        if project.owner != request.user:
            return Response(
                {"detail": "Vous n'êtes pas autorisé à supprimer des membres de l'équipe de ce projet."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        member_id = request.data.get('member_id')
        if not member_id:
            return Response(
                {"detail": "L'ID du membre est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            team_member = project.team_members.get(id=member_id)
            team_member.delete()
            return Response({"detail": "Membre supprimé avec succès."}, status=status.HTTP_204_NO_CONTENT)
        except TeamMember.DoesNotExist:
            return Response(
                {"detail": "Membre non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def list_team_members(self, request, pk=None):
        """
        Lister les membres de l'équipe du projet
        """
        project = self.get_object()
        team_members = project.team_members.all()
        serializer = ProjectTeamMemberSerializer(team_members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
