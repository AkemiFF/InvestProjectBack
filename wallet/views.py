import stripe
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from investments.models import Transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Wallet, WalletTransaction
from .serializers import (DepositSerializer, WalletSerializer,
                          WalletTransactionSerializer)

stripe.api_key = settings.STRIPE_SECRET_KEY

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les portefeuilles
    """
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Retourne le portefeuille de l'utilisateur connecté
        """
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """
        Récupère le portefeuille de l'utilisateur connecté
        """
        try:
            wallet = Wallet.objects.get(user=request.user)
            serializer = self.get_serializer(wallet)
            return Response(serializer.data)
        except Wallet.DoesNotExist:
            # Créer un portefeuille si l'utilisateur n'en a pas
            wallet = Wallet.objects.create(user=request.user)
            serializer = self.get_serializer(wallet)
            return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """
        Récupère les transactions du portefeuille de l'utilisateur connecté
        """
        try:
            wallet = Wallet.objects.get(user=request.user)
            transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
            
            # Pagination
            page = self.paginate_queryset(transactions)
            if page is not None:
                serializer = WalletTransactionSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = WalletTransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        except Wallet.DoesNotExist:
            return Response({"detail": "Portefeuille non trouvé."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def create_deposit_intent(self, request):
        """
        Crée une intention de dépôt avec Stripe
        """
        try:
            amount = request.data.get('amount')
            if not amount:
                return Response({"detail": "Le montant est requis."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Convertir en centimes pour Stripe
            amount_cents = int(float(amount) * 100)
            
            # Créer une intention de paiement Stripe
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='eur',
                metadata={
                    'user_id': request.user.id,
                    'transaction_type': 'deposit'
                }
            )
            
            # Créer une transaction en attente
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='deposit',
                amount=amount,
                status='pending',
                reference_id=intent.id
            )
            
            return Response({
                'clientSecret': intent.client_secret,
                'transaction_id': transaction.id
            })
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def confirm_deposit(self, request):
        """
        Confirme un dépôt après paiement Stripe réussi
        """
        try:
            payment_intent_id = request.data.get('payment_intent_id')
            if not payment_intent_id:
                return Response({"detail": "L'ID d'intention de paiement est requis."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier l'intention de paiement Stripe
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status != 'succeeded':
                return Response({"detail": "Le paiement n'a pas été confirmé."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Mettre à jour la transaction
            with transaction.atomic():
                try:
                    trans = Transaction.objects.get(reference_id=payment_intent_id)
                    
                    if trans.status == 'completed':
                        return Response({"detail": "Ce dépôt a déjà été traité."}, status=status.HTTP_400_BAD_REQUEST)
                    
                    trans.status = 'completed'
                    trans.completed_at = timezone.now()
                    trans.save()
                    
                    # Mettre à jour le portefeuille
                    wallet = Wallet.objects.get(user=request.user)
                    wallet.deposit(trans.amount)
                    
                    # Créer une transaction de portefeuille
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='deposit',
                        amount=trans.amount
                    )
                    
                    return Response({"status": "Dépôt confirmé avec succès."})
                except Transaction.DoesNotExist:
                    return Response({"detail": "Transaction non trouvée."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def stripe_webhook(self, request):
        """
        Webhook pour les événements Stripe
        """
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Traiter l'événement
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                
                # Vérifier que c'est un dépôt
                if payment_intent.metadata.get('transaction_type') == 'deposit':
                    user_id = payment_intent.metadata.get('user_id')
                    
                    # Mettre à jour la transaction
                    with transaction.atomic():
                        try:
                            trans = Transaction.objects.get(reference_id=payment_intent.id)
                            
                            if trans.status == 'completed':
                                return HttpResponse(status=200)
                            
                            trans.status = 'completed'
                            trans.completed_at = timezone.now()
                            trans.save()
                            
                            # Mettre à jour le portefeuille
                            wallet = Wallet.objects.get(user_id=user_id)
                            wallet.deposit(trans.amount)
                            
                            # Créer une transaction de portefeuille
                            WalletTransaction.objects.create(
                                wallet=wallet,
                                transaction_type='deposit',
                                amount=trans.amount
                            )
                        except (Transaction.DoesNotExist, Wallet.DoesNotExist):
                            pass
            
            return HttpResponse(status=200)
        except ValueError as e:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            return HttpResponse(status=400)
