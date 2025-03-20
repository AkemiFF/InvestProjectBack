# admin_dashboard/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import AdminLog, SystemSetting, Statistic
from .serializers import (
    AdminLogSerializer, SystemSettingSerializer, StatisticSerializer,
    DashboardMetricsSerializer, UserManagementSerializer,
    ProjectManagementSerializer, CommentModerationSerializer
)
from .permissions import IsAdminUser
from .utils import (
    log_admin_action, get_dashboard_metrics, get_user_growth_data,
    get_revenue_data, update_daily_statistics
)

class AdminLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les journaux d'administration
    """
    queryset = AdminLog.objects.all().order_by('-created_at')
    serializer_class = AdminLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['action_type', 'description', 'admin_user__username']
    ordering_fields = ['created_at', 'action_type']
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Récupère les journaux d'administration par type d'action
        """
        action_type = request.query_params.get('type')
        if not action_type:
            return Response(
                {"detail": "Le paramètre 'type' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(action_type=action_type)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """
        Récupère les journaux d'administration par utilisateur
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {"detail": "Le paramètre 'user_id' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(admin_user_id=user_id)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class SystemSettingViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les paramètres système
    """
    serializer_class = SystemSettingSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """
        Retourne tous les paramètres système pour les administrateurs,
        ou seulement les paramètres publics pour les utilisateurs normaux
        """
        if self.request.user.is_staff:
            return SystemSetting.objects.all().order_by('key')
        else:
            return SystemSetting.objects.filter(is_public=True).order_by('key')
    
    def perform_create(self, serializer):
        """
        Associe l'utilisateur connecté au paramètre système lors de la création
        """
        serializer.save(updated_by=self.request.user)
    
    def perform_update(self, serializer):
        """
        Associe l'utilisateur connecté au paramètre système lors de la mise à jour
        """
        serializer.save(updated_by=self.request.user)
        
        # Enregistrer l'action dans le journal
        log_admin_action(
            admin_user=self.request.user,
            action_type='system_config',
            description=f"Mise à jour du paramètre système '{serializer.instance.key}'",
            related_object=serializer.instance,
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    @action(detail=False, methods=['get'])
    def public(self, request):
        """
        Récupère les paramètres système publics
        """
        queryset = SystemSetting.objects.filter(is_public=True).order_by('key')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_key(self, request):
        """
        Récupère un paramètre système par sa clé
        """
        key = request.query_params.get('key')
        if not key:
            return Response(
                {"detail": "Le paramètre 'key' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            setting = self.get_queryset().get(key=key)
            serializer = self.get_serializer(setting)
            return Response(serializer.data)
        except SystemSetting.DoesNotExist:
            return Response(
                {"detail": "Paramètre système non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )

class StatisticViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les statistiques
    """
    queryset = Statistic.objects.all().order_by('-date')
    serializer_class = StatisticSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date', 'stat_type', 'value']
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Récupère les statistiques par type
        """
        stat_type = request.query_params.get('type')
        if not stat_type:
            return Response(
                {"detail": "Le paramètre 'type' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(stat_type=stat_type).order_by('-date')
        
        # Limiter le nombre de résultats si demandé
        limit = request.query_params.get('limit')
        if limit:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except ValueError:
                pass
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """
        Récupère les statistiques par date
        """
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {"detail": "Le paramètre 'date' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Format de date invalide. Utilisez le format YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(date=date)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_daily(self, request):
        """
        Met à jour les statistiques quotidiennes
        """
        success = update_daily_statistics()
        
        if success:
            # Enregistrer l'action dans le journal
            log_admin_action(
                admin_user=request.user,
                action_type='system_config',
                description="Mise à jour des statistiques quotidiennes",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({"status": "Statistiques mises à jour avec succès."})
        else:
            return Response(
                {"detail": "Erreur lors de la mise à jour des statistiques."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DashboardViewSet(viewsets.ViewSet):
    """
    API endpoint pour le tableau de bord administratif
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """
        Récupère les métriques pour le tableau de bord
        """
        metrics = get_dashboard_metrics()
        serializer = DashboardMetricsSerializer(metrics)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_growth(self, request):
        """
        Récupère les données de croissance des utilisateurs
        """
        period = request.query_params.get('period', 'month')
        limit = request.query_params.get('limit', 12)
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 12
        
        data = get_user_growth_data(period=period, limit=limit)
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def revenue_data(self, request):
        """
        Récupère les données de revenus
        """
        period = request.query_params.get('period', 'month')
        limit = request.query_params.get('limit', 12)
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 12
        
        data = get_revenue_data(period=period, limit=limit)
        return Response(data)

class UserManagementViewSet(viewsets.ViewSet):
    """
    API endpoint pour la gestion des utilisateurs
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def list_users(self, request):
        """
        Liste tous les utilisateurs avec filtres
        """
        from users.models import User
        from users.serializers import UserProfileSerializer
        
        # Filtres
        status = request.query_params.get('status')
        role = request.query_params.get('role')
        search = request.query_params.get('search')
        
        queryset = User.objects.all()
        
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'verified':
            queryset = queryset.filter(is_verified=True)
        elif status == 'unverified':
            queryset = queryset.filter(is_verified=False)
        
        if role == 'admin':
            queryset = queryset.filter(is_staff=True)
        elif role == 'investor':
            queryset = queryset.filter(is_investor=True)
        elif role == 'project_owner':
            queryset = queryset.filter(is_project_owner=True)
        
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 10))
        page = int(request.query_params.get('page', 1))
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        total_count = queryset.count()
        queryset = queryset.order_by('-date_joined')[start_idx:end_idx]
        
        serializer = UserProfileSerializer(queryset, many=True)
        
        return Response({
            'count': total_count,
            'next': page < (total_count // page_size) + 1,
            'previous': page > 1,
            'results': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def manage_user(self, request):
        """
        Gère un utilisateur (activation, désactivation, etc.)
        """
        serializer = UserManagementSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        from users.serializers import UserProfileSerializer
        return Response(UserProfileSerializer(user).data)

class ProjectManagementViewSet(viewsets.ViewSet):
    """
    API endpoint pour la gestion des projets
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def list_projects(self, request):
        """
        Liste tous les projets avec filtres
        """
        from projects.models import Project
        from projects.serializers import ProjectListSerializer
        
        # Filtres
        status = request.query_params.get('status')
        featured = request.query_params.get('featured')
        hidden = request.query_params.get('hidden')
        search = request.query_params.get('search')
        
        queryset = Project.objects.all()
        
        if status:
            queryset = queryset.filter(status=status)
        
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)
        elif featured == 'false':
            queryset = queryset.filter(is_featured=False)
        
        if hidden == 'true':
            queryset = queryset.filter(is_hidden=True)
        elif hidden == 'false':
            queryset = queryset.filter(is_hidden=False)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(owner__username__icontains=search)
            )
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 10))
        page = int(request.query_params.get('page', 1))
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        total_count = queryset.count()
        queryset = queryset.order_by('-created_at')[start_idx:end_idx]
        
        serializer = ProjectListSerializer(queryset, many=True)
        
        return Response({
            'count': total_count,
            'next': page < (total_count // page_size) + 1,
            'previous': page > 1,
            'results': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def manage_project(self, request):
        """
        Gère un projet (approbation, rejet, etc.)
        """
        serializer = ProjectManagementSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        
        from projects.serializers import ProjectDetailSerializer
        return Response(ProjectDetailSerializer(project).data)

class CommentModerationViewSet(viewsets.ViewSet):
    """
    API endpoint pour la modération des commentaires
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def list_reported_comments(self, request):
        """
        Liste tous les commentaires signalés
        """
        from comments.models import Comment
        from comments.serializers import CommentSerializer
        
        queryset = Comment.objects.filter(is_reported=True, is_moderated=False)
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 10))
        page = int(request.query_params.get('page', 1))
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        total_count = queryset.count()
        queryset = queryset.order_by('-created_at')[start_idx:end_idx]
        
        serializer = CommentSerializer(queryset, many=True)
        
        return Response({
            'count': total_count,
            'next': page < (total_count // page_size) + 1,
            'previous': page > 1,
            'results': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def moderate_comment(self, request):
        """
        Modère un commentaire (approbation, rejet, etc.)
        """
        serializer = CommentModerationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        
        from comments.serializers import CommentSerializer
        return Response(CommentSerializer(comment).data)