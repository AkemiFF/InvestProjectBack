# subscriptions/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import SubscriptionPlan, Subscription, ProjectBoost
from .serializers import (
    SubscriptionPlanSerializer, SubscriptionSerializer, SubscriptionCreateSerializer,
    ProjectBoostSerializer, ProjectBoostCreateSerializer
)
from .permissions import IsSubscriptionOwner, IsProjectBoostOwner
from .utils import check_subscription_status, check_project_boost_status, get_user_subscription_type
from notifications.utils import create_system_notification

class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les plans d'abonnement
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['price', 'duration_days']
    ordering = ['price']
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Récupère les plans d'abonnement par type
        """
        plan_type = request.query_params.get('type')
        if not plan_type:
            return Response(
                {"detail": "Le paramètre 'type' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(plan_type=plan_type)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les abonnements
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsSubscriptionOwner]
    
    def get_queryset(self):
        """
        Retourne les abonnements de l'utilisateur connecté
        """
        user = self.request.user
        
        # Si l'utilisateur est un administrateur, il peut voir tous les abonnements
        if user.is_staff:
            return Subscription.objects.all()
        
        # Sinon, l'utilisateur voit ses propres abonnements
        return Subscription.objects.filter(user=user)
    
    def get_serializer_class(self):
        """
        Utilise différents sérialiseurs en fonction de l'action
        """
        if self.action == 'create' or self.action == 'subscribe':
            return SubscriptionCreateSerializer
        return SubscriptionSerializer
    
    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """
        S'abonne à un plan
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        
        return Response(
            SubscriptionSerializer(subscription, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Annule un abonnement
        """
        subscription = self.get_object()
        
        # Vérifier que l'abonnement est actif
        if subscription.status != 'active':
            return Response(
                {"detail": "Seuls les abonnements actifs peuvent être annulés."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Annuler l'abonnement
        subscription.status = 'cancelled'
        subscription.auto_renew = False
        subscription.save(update_fields=['status', 'auto_renew'])
        
        # Créer une notification
        create_system_notification(
            recipient=request.user,
            title="Abonnement annulé",
            message=f"Votre abonnement {subscription.plan.name} a été annulé. Vous pouvez continuer à utiliser les fonctionnalités jusqu'au {subscription.end_date.strftime('%d/%m/%Y')}."
        )
        
        return Response({"status": "Abonnement annulé avec succès."})
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """
        Renouvelle un abonnement
        """
        subscription = self.get_object()
        
        # Vérifier que l'abonnement peut être renouvelé
        if subscription.status not in ['active', 'expired']:
            return Response(
                {"detail": "Seuls les abonnements actifs ou expirés peuvent être renouvelés."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Renouveler l'abonnement
        if subscription.status == 'expired':
            # Si l'abonnement est expiré, créer une nouvelle période
            subscription.start_date = timezone.now()
            subscription.end_date = subscription.start_date + timezone.timedelta(days=subscription.plan.duration_days)
            subscription.status = 'active'
        else:
            # Si l'abonnement est actif, prolonger la période
            subscription.end_date = subscription.end_date + timezone.timedelta(days=subscription.plan.duration_days)
        
        # Activer le renouvellement automatique si demandé
        auto_renew = request.data.get('auto_renew')
        if auto_renew is not None:
            subscription.auto_renew = auto_renew
        
        subscription.save(update_fields=['start_date', 'end_date', 'status', 'auto_renew'])
        
        # Créer une notification
        create_system_notification(
            recipient=request.user,
            title="Abonnement renouvelé",
            message=f"Votre abonnement {subscription.plan.name} a été renouvelé et est valable jusqu'au {subscription.end_date.strftime('%d/%m/%Y')}."
        )
        
        return Response(SubscriptionSerializer(subscription, context={'request': request}).data)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Récupère l'abonnement actif de l'utilisateur
        """
        subscription = check_subscription_status(request.user)
        
        if not subscription:
            return Response(
                {"detail": "Vous n'avez pas d'abonnement actif."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SubscriptionSerializer(subscription, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Récupère l'historique des abonnements de l'utilisateur
        """
        queryset = Subscription.objects.filter(user=request.user).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = SubscriptionSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Vérifie le statut de l'abonnement de l'utilisateur
        """
        subscription_type = get_user_subscription_type(request.user)
        
        subscription = check_subscription_status(request.user)
        
        if subscription:
            days_left = (subscription.end_date - timezone.now().date()).days
            return Response({
                'has_subscription': True,
                'subscription_type': subscription_type,
                'plan_name': subscription.plan.name,
                'days_left': days_left,
                'end_date': subscription.end_date,
                'auto_renew': subscription.auto_renew
            })
        else:
            return Response({
                'has_subscription': False,
                'subscription_type': 'basic'
            })

class ProjectBoostViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les boosts de projets
    """
    serializer_class = ProjectBoostSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectBoostOwner]
    
    def get_queryset(self):
        """
        Retourne les boosts de projets de l'utilisateur connecté
        """
        user = self.request.user
        
        # Si l'utilisateur est un administrateur, il peut voir tous les boosts
        if user.is_staff:
            return ProjectBoost.objects.all()
        
        # Sinon, l'utilisateur voit les boosts de ses propres projets
        return ProjectBoost.objects.filter(project__owner=user)
    
    def get_serializer_class(self):
        """
        Utilise différents sérialiseurs en fonction de l'action
        """
        if self.action == 'create' or self.action == 'boost_project':
            return ProjectBoostCreateSerializer
        return ProjectBoostSerializer
    
    @action(detail=False, methods=['post'])
    def boost_project(self, request):
        """
        Booste un projet
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        boost = serializer.save()
        
        return Response(
            ProjectBoostSerializer(boost, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Annule un boost de projet
        """
        boost = self.get_object()
        
        # Vérifier que le boost est actif
        if not boost.is_active:
            return Response(
                {"detail": "Ce boost n'est pas actif."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Annuler le boost
        boost.is_active = False
        boost.end_date = timezone.now()
        boost.save(update_fields=['is_active', 'end_date'])
        
        # Vérifier s'il y a d'autres boosts actifs pour ce projet
        active_boosts = ProjectBoost.objects.filter(
            project=boost.project,
            is_active=True,
            end_date__gte=timezone.now()
        ).exists()
        
        # Si aucun autre boost actif, mettre à jour le statut du projet
        if not active_boosts:
            boost.project.is_boosted = False
            boost.project.save(update_fields=['is_boosted'])
        
        # Créer une notification
        create_system_notification(
            recipient=request.user,
            title="Boost annulé",
            message=f"Le boost de votre projet '{boost.project.title}' a été annulé."
        )
        
        return Response({"status": "Boost annulé avec succès."})
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Récupère les boosts actifs de l'utilisateur
        """
        queryset = ProjectBoost.objects.filter(
            project__owner=request.user,
            is_active=True,
            end_date__gte=timezone.now()
        ).order_by('end_date')
        
        serializer = ProjectBoostSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Récupère l'historique des boosts de l'utilisateur
        """
        queryset = ProjectBoost.objects.filter(
            project__owner=request.user
        ).order_by('-start_date')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProjectBoostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProjectBoostSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def project_boosts(self, request):
        """
        Récupère les boosts d'un projet spécifique
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"detail": "Le paramètre 'project_id' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que le projet appartient à l'utilisateur
        from projects.models import Project
        try:
            project = Project.objects.get(id=project_id)
            if project.owner != request.user and not request.user.is_staff:
                return Response(
                    {"detail": "Vous n'êtes pas autorisé à voir les boosts de ce projet."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Project.DoesNotExist:
            return Response(
                {"detail": "Le projet spécifié n'existe pas."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        queryset = ProjectBoost.objects.filter(project_id=project_id).order_by('-start_date')
        
        serializer = ProjectBoostSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)