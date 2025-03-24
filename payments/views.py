# payments/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import PaymentMethod, Invoice
from .serializers import (
    PaymentMethodSerializer, PaymentMethodCreateSerializer,
    InvoiceSerializer, PaymentProcessSerializer, TransactionSerializer
)
from .permissions import IsPaymentMethodOwner, IsInvoiceOwner
from .utils import create_invoice, get_user_transactions, generate_receipt_data
from notifications.utils import create_system_notification

class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les méthodes de paiement
    """
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated, IsPaymentMethodOwner]
    
    def get_queryset(self):
        """
        Retourne les méthodes de paiement de l'utilisateur connecté
        """
        return PaymentMethod.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """
        Utilise différents sérialiseurs en fonction de l'action
        """
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return PaymentMethodCreateSerializer
        return PaymentMethodSerializer
    
    def perform_create(self, serializer):
        """
        Associe l'utilisateur connecté à la méthode de paiement lors de la création
        """
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Définit une méthode de paiement comme méthode par défaut
        """
        payment_method = self.get_object()
        
        # Désactiver les autres méthodes par défaut
        PaymentMethod.objects.filter(user=request.user, is_default=True).update(is_default=False)
        
        # Définir cette méthode comme par défaut
        payment_method.is_default = True
        payment_method.save(update_fields=['is_default'])
        
        return Response({"status": "Méthode de paiement définie comme par défaut."})
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """
        Récupère la méthode de paiement par défaut de l'utilisateur
        """
        payment_method = PaymentMethod.objects.filter(user=request.user, is_default=True).first()
        
        if not payment_method:
            return Response(
                {"detail": "Aucune méthode de paiement par défaut n'est définie."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(payment_method)
        return Response(serializer.data)

class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les factures
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsInvoiceOwner]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['issue_date', 'due_date', 'amount']
    ordering = ['-issue_date']
    
    def get_queryset(self):
        """
        Retourne les factures de l'utilisateur connecté
        """
        user = self.request.user
        
        # Si l'utilisateur est un administrateur, il peut voir toutes les factures
        if user.is_staff:
            return Invoice.objects.all()
        
        # Sinon, l'utilisateur voit ses propres factures
        return Invoice.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Récupère les factures en attente de paiement
        """
        queryset = self.get_queryset().filter(
            Q(status='sent') | Q(status='overdue')
        ).order_by('due_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def paid(self, request):
        """
        Récupère les factures payées
        """
        queryset = self.get_queryset().filter(status='paid').order_by('-paid_date')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        """
        Génère un reçu pour une facture payée
        """
        invoice = self.get_object()
        
        if invoice.status != 'paid':
            return Response(
                {"detail": "Impossible de générer un reçu pour une facture non payée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        receipt_data = generate_receipt_data(invoice)
        
        return Response(receipt_data)

class PaymentProcessViewSet(viewsets.ViewSet):
    """
    API endpoint pour le traitement des paiements
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def process_payment(self, request):
        """
        Traite un paiement
        """
        serializer = PaymentProcessSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()
        
        return Response(
            {"status": "Paiement effectué avec succès.", "invoice_id": invoice.id},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """
        Récupère l'historique des transactions de l'utilisateur
        """
        transactions = get_user_transactions(request.user)
        
        # Pagination manuelle
        page_size = int(request.query_params.get('page_size', 10))
        page = int(request.query_params.get('page', 1))
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_transactions = transactions[start_idx:end_idx]
        
        serializer = TransactionSerializer(paginated_transactions, many=True)
        
        return Response({
            'count': len(transactions),
            'next': page < (len(transactions) // page_size) + 1,
            'previous': page > 1,
            'results': serializer.data
        })