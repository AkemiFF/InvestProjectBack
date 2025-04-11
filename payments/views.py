# payments/views.py
import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from investments.models import Investment
from notifications.utils import create_system_notification
from projects.models import Project
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Invoice, PaymentMethod
from .permissions import IsInvoiceOwner, IsPaymentMethodOwner
from .serializers import (InvoiceSerializer, PaymentMethodCreateSerializer,
                          PaymentMethodSerializer, PaymentProcessSerializer,
                          TransactionSerializer)
from .utils import create_invoice, generate_receipt_data, get_user_transactions

# Configurer Stripe avec votre clé secrète
stripe.api_key = settings.STRIPE_SECRET_KEY
# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# You can add handlers here if needed, e.g., FileHandler or StreamHandler
class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            data = request.data
            amount = int(data.get('amount', 0))  # Montant en centimes
            currency = data.get('currency', 'mga').lower()
            metadata = data.get('metadata', {})
            
            # Ajouter l'ID de l'utilisateur aux métadonnées
            metadata['user_id'] = str(request.user.id)
            
            # Créer l'intention de paiement
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata,
                payment_method_types=['card'],
            )
            
            return Response({
                'success': True,
                'data': {
                    'id': intent.id,
                    'client_secret': intent.client_secret,
                    'amount': intent.amount,
                    'currency': intent.currency,
                    'status': intent.status,
                    'payment_method_types': intent.payment_method_types,
                }
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            data = request.data
            amount = int(data.get('amount', 0))  # Montant en centimes
            currency = data.get('currency', 'mga').lower()
            metadata = data.get('metadata', {})
            success_url = data.get('success_url')
            cancel_url = data.get('cancel_url')
            
            if not success_url or not cancel_url:
                return Response({
                    'success': False,
                    'message': 'Les URLs de succès et d\'annulation sont requises'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Ajouter l'ID de l'utilisateur aux métadonnées
            metadata['user_id'] = str(request.user.id)
            
            # Créer la session de paiement
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': 'Investissement',
                            'description': 'Investissement dans un projet',
                        },
                        'unit_amount': amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
            )
            
            return Response({
                'success': True,
                'data': {
                    'id': session.id,
                    'url': session.url,
                    'payment_intent_id': session.payment_intent,
                    'amount': amount,
                    'currency': currency,
                    'status': session.status,
                }
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, payment_id):
        try:
            # Récupérer les détails de l'intention de paiement
            intent = stripe.PaymentIntent.retrieve(payment_id)
            
            return Response({
                'success': True,
                'data': {
                    'id': intent.id,
                    'amount': intent.amount,
                    'currency': intent.currency,
                    'status': intent.status,
                    'payment_method_types': intent.payment_method_types,
                }
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CheckSessionStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        try:
            # Récupérer les détails de la session de paiement
            session = stripe.checkout.Session.retrieve(session_id)
            
            return Response({
                'success': True,
                'data': {
                    'id': session.id,
                    'payment_intent': session.payment_intent,
                    'amount': session.amount_total,
                    'currency': session.currency,
                    'status': session.status,
                    'customer': session.customer,
                    'metadata': session.metadata,
                }
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ConfirmPaymentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, payment_id):
        try:
            # Confirmer l'intention de paiement
            intent = stripe.PaymentIntent.confirm(payment_id)
            
            return Response({
                'success': True,
                'data': {
                    'id': intent.id,
                    'status': intent.status,
                }
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SavedPaymentMethodsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Récupérer le client Stripe associé à l'utilisateur
            customer = self._get_or_create_customer(request.user)
            
            # Récupérer les méthodes de paiement enregistrées
            payment_methods = stripe.PaymentMethod.list(
                customer=customer.id,
                type="card",
            )
            
            return Response({
                'success': True,
                'data': payment_methods.data
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_or_create_customer(self, user):
        # Récupérer ou créer un client Stripe pour l'utilisateur
        # Cette fonction dépend de votre modèle utilisateur
        # et de la façon dont vous stockez l'ID client Stripe
        
        # Exemple simplifié:
        if hasattr(user, 'stripe_customer_id') and user.stripe_customer_id:
            return stripe.Customer.retrieve(user.stripe_customer_id)
        else:
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                metadata={
                    'user_id': str(user.id)
                }
            )
            
            # Enregistrer l'ID client dans votre modèle utilisateur
            user.stripe_customer_id = customer.id
            user.save()
            
            return customer

class SavePaymentMethodView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            payment_method_id = request.data.get('payment_method_id')
            
            if not payment_method_id:
                return Response({
                    'success': False,
                    'message': 'ID de méthode de paiement requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer ou créer le client Stripe
            customer = self._get_or_create_customer(request.user)
            
            # Attacher la méthode de paiement au client
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer.id,
            )
            
            return Response({
                'success': True,
                'data': payment_method
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_or_create_customer(self, user):
        # Même fonction que dans SavedPaymentMethodsView
        if hasattr(user, 'stripe_customer_id') and user.stripe_customer_id:
            return stripe.Customer.retrieve(user.stripe_customer_id)
        else:
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                metadata={
                    'user_id': str(user.id)
                }
            )
            
            user.stripe_customer_id = customer.id
            user.save()
            
            return customer

class DeletePaymentMethodView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, payment_method_id):
        try:
            # Détacher la méthode de paiement
            payment_method = stripe.PaymentMethod.detach(payment_method_id)
            
            return Response({
                'success': True,
                'data': {
                    'success': True,
                    'id': payment_method.id
                }
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    logging.info(f"Received webhook: {payload}")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        # Gérer les différents types d'événements
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            handle_payment_success(payment_intent)
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            handle_payment_failure(payment_intent)
        elif event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_checkout_success(session)
        
        return JsonResponse({'status': 'success'})
    
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def handle_payment_success(payment_intent):
    """
    Gérer un paiement réussi
    """
    # Récupérer les métadonnées
    metadata = payment_intent.get('metadata', {})
    project_id = metadata.get('project_id')
    user_id = metadata.get('user_id')
    
    # Mettre à jour votre base de données
    # Par exemple, créer un investissement ou mettre à jour son statut
    
    # Exemple simplifié:
    from django.contrib.auth import get_user_model
    from investments.models import Investment
    from projects.models import Project
    
    User = get_user_model()
    
    try:
        if project_id and user_id:
            user = User.objects.get(id=user_id)
            project = Project.objects.get(id=project_id)
            
            # Créer ou mettre à jour l'investissement
            investment, created = Investment.objects.get_or_create(
                payment_intent_id=payment_intent.id,
                defaults={
                    'user': user,
                    'project': project,
                    'amount': Decimal(payment_intent.amount) / 100,  # Convertir les centimes en unités
                    'status': 'completed',
                }
            )
            
            if not created:
                investment.status = 'completed'
                investment.save()
    except Exception as e:
        # Gérer les erreurs et les journaliser
        print(f"Error handling payment success: {str(e)}")

def handle_payment_failure(payment_intent):
    """
    Gérer un paiement échoué
    """
    # Mettre à jour votre base de données
    # Par exemple, marquer un investissement comme échoué
    
    # Exemple simplifié:
    from investments.models import Investment
    
    try:
        investment = Investment.objects.filter(payment_intent_id=payment_intent.id).first()
        if investment:
            investment.status = 'failed'
            investment.save()
    except Exception as e:
        print(f"Error handling payment failure: {str(e)}")

def handle_checkout_success(session):
    """
    Gérer une session de paiement Stripe Checkout réussie
    """
    # Récupérer les métadonnées
    metadata = session.get('metadata', {})
    project_id = metadata.get('project_id')
    user_id = metadata.get('user_id')
    
    # Mettre à jour votre base de données
    # Exemple simplifié:

    User = get_user_model()
    
    try:
        if project_id and user_id:
            user = User.objects.get(id=user_id)
            project = Project.objects.get(id=project_id)
            
            # Créer ou mettre à jour l'investissement
            investment, created = Investment.objects.get_or_create(
                payment_session_id=session.id,
                defaults={
                    'user': user,
                    'project': project,
                    'amount': Decimal(session.amount_total) / 100,
                    'status': 'completed',
                    'payment_intent_id': session.payment_intent,
                }
            )
            
            if not created:
                investment.status = 'completed'
                investment.payment_intent_id = session.payment_intent
                investment.save()
    except Exception as e:
        print(f"Error handling checkout success: {str(e)}")

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