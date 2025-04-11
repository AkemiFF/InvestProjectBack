# investments/views.py
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django_filters.rest_framework import DjangoFilterBackend
from notifications.utils import create_system_notification
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Investment, Transaction
from .permissions import IsInvestmentParticipant, IsTransactionOwner
from .serializers import (DepositSerializer, InvestmentCreateSerializer,
                          InvestmentSerializer, TransactionSerializer,
                          WithdrawalSerializer)
from .utils import (calculate_user_balance, update_project_amount_raised,
                    update_project_owner_stats, update_user_investment_stats)


class InvestmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les investissements
    """
    serializer_class = InvestmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsInvestmentParticipant]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'project']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Retourne les investissements de l'utilisateur ou des projets de l'utilisateur
        """
        user = self.request.user
        
        # Si l'utilisateur est un administrateur, il peut voir tous les investissements
        if user.is_staff:
            return Investment.objects.all()
        
        # Sinon, l'utilisateur voit ses propres investissements et ceux de ses projets
        return Investment.objects.filter(
            Q(investor=user) | Q(project__owner=user)
        )
    
    def get_serializer_class(self):
        """
        Utilise différents sérialiseurs en fonction de l'action
        """
        if self.action == 'create':
            return InvestmentCreateSerializer
        return InvestmentSerializer
    
    @action(detail=False, methods=['get'])
    def my_investments(self, request):
        """
        Récupère les investissements de l'utilisateur connecté
        """
        queryset = Investment.objects.filter(user=request.user)
        
        # Filtrer par statut si spécifié
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtrer par projet si spécifié
        project_param = request.query_params.get('project')
        if project_param:
            queryset = queryset.filter(project_id=project_param)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def project_investments(self, request):
        """
        Récupère les investissements pour les projets de l'utilisateur connecté
        """
        queryset = Investment.objects.filter(project__owner=request.user)
        
        # Filtrer par statut si spécifié
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtrer par projet si spécifié
        project_param = request.query_params.get('project')
        if project_param:
            queryset = queryset.filter(project_id=project_param)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Annule un investissement en attente
        """
        investment = self.get_object()
        
        # Vérifier que l'investissement est en attente
        if investment.status != 'pending':
            return Response(
                {"detail": "Seuls les investissements en attente peuvent être annulés."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que l'utilisateur est l'investisseur
        if investment.user != request.user:
            return Response(
                {"detail": "Vous ne pouvez annuler que vos propres investissements."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            # Mettre à jour le statut de l'investissement
            investment.status = 'cancelled'
            investment.save(update_fields=['status'])
            
            # Mettre à jour le statut des transactions associées
            Transaction.objects.filter(investment=investment).update(status='cancelled')
            
            # Créer une notification pour le propriétaire du projet
            create_system_notification(
                recipient=investment.project.owner,
                title="Investissement annulé",
                message=f"L'investissement de {investment.user.first_name} {investment.user.last_name} de {investment.amount} dans votre projet '{investment.project.title}' a été annulé."
            )
        
        return Response({"status": "Investissement annulé avec succès."})
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirme un investissement en attente (admin ou système uniquement)
        """
        investment = self.get_object()
        
        # Vérifier que l'utilisateur est un administrateur
        if not request.user.is_staff:
            return Response(
                {"detail": "Seuls les administrateurs peuvent confirmer les investissements."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que l'investissement est en attente
        if investment.status != 'pending':
            return Response(
                {"detail": "Seuls les investissements en attente peuvent être confirmés."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Mettre à jour le statut de l'investissement
            investment.status = 'completed'
            investment.save(update_fields=['status'])
            
            # Mettre à jour le statut des transactions associées
            Transaction.objects.filter(investment=investment).update(status='completed')
            
            # Mettre à jour le montant collecté du projet
            update_project_amount_raised(investment.project)
            
            # Mettre à jour les statistiques de l'investisseur
            update_user_investment_stats(investment.user)
            
            # Mettre à jour les statistiques du porteur de projet
            update_project_owner_stats(investment.project.owner)
            
            # Créer des notifications
            create_system_notification(
                recipient=investment.user,
                title="Investissement confirmé",
                message=f"Votre investissement de {investment.amount} dans le projet '{investment.project.title}' a été confirmé."
            )
            
            create_system_notification(
                recipient=investment.project.owner,
                title="Investissement confirmé",
                message=f"L'investissement de {investment.user.first_name} {investment.user.last_name} de {investment.amount} dans votre projet '{investment.project.title}' a été confirmé."
            )
        
        return Response({"status": "Investissement confirmé avec succès."})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Récupère des statistiques sur les investissements de l'utilisateur
        """
        user = request.user
        
        # Statistiques pour les investisseurs
        if hasattr(user, 'investor_profile'):
            total_invested = Investment.objects.filter(
                investor=user,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            projects_count = Investment.objects.filter(
                investor=user,
                status='completed'
            ).values('project').distinct().count()
            
            pending_investments = Investment.objects.filter(
                investor=user,
                status='pending'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            return Response({
                'total_invested': total_invested,
                'projects_supported': projects_count,
                'pending_investments': pending_investments,
                'balance': calculate_user_balance(user)
            })
        
        # Statistiques pour les porteurs de projet
        elif hasattr(user, 'project_owner_profile'):
            total_raised = Investment.objects.filter(
                project__owner=user,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            investors_count = Investment.objects.filter(
                project__owner=user,
                status='completed'
            ).values('investor').distinct().count()
            
            pending_investments = Investment.objects.filter(
                project__owner=user,
                status='pending'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            return Response({
                'total_raised': total_raised,
                'unique_investors': investors_count,
                'pending_investments': pending_investments,
                'balance': calculate_user_balance(user)
            })
        
        return Response({"detail": "Profil utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les transactions
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsTransactionOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'status']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retourne les transactions de l'utilisateur connecté
        """
        user = self.request.user
        
        # Si l'utilisateur est un administrateur, il peut voir toutes les transactions
        if user.is_staff:
            return Transaction.objects.all()
        
        # Sinon, l'utilisateur voit ses propres transactions
        return Transaction.objects.filter(user=user)
    
    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """
        Crée une transaction de dépôt
        """
        serializer = DepositSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()
        
        # Dans un système réel, ici vous redirigeriez vers une passerelle de paiement
        # Pour cet exemple, nous simulons une transaction réussie
        transaction.status = 'completed'
        transaction.save(update_fields=['status'])
        
        # Mettre à jour le solde de l'utilisateur
        if hasattr(request.user, 'investor_profile'):
            request.user.investor_profile.balance = calculate_user_balance(request.user)
            request.user.investor_profile.save(update_fields=['balance'])
        
        if hasattr(request.user, 'project_owner_profile'):
            request.user.project_owner_profile.balance = calculate_user_balance(request.user)
            request.user.project_owner_profile.save(update_fields=['balance'])
        
        # Créer une notification
        create_system_notification(
            recipient=request.user,
            title="Dépôt effectué",
            message=f"Votre dépôt de {transaction.amount} a été effectué avec succès."
        )
        
        return Response(TransactionSerializer(transaction, context={'request': request}).data)
    
    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """
        Crée une transaction de retrait
        """
        serializer = WithdrawalSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()
        
        # Dans un système réel, ici vous initieriez un virement bancaire
        # Pour cet exemple, nous laissons la transaction en attente
        
        # Créer une notification
        create_system_notification(
            recipient=request.user,
            title="Demande de retrait",
            message=f"Votre demande de retrait de {transaction.amount} a été enregistrée et est en cours de traitement."
        )
        
        return Response(TransactionSerializer(transaction, context={'request': request}).data)
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """
        Récupère le solde de l'utilisateur
        """
        balance = calculate_user_balance(request.user)
        
        return Response({
            'balance': balance
        })