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
from .serializers import *

stripe.api_key = settings.STRIPE_SECRET_KEY
from decimal import Decimal

from djmoney.money import Money

WITHDRAWAL_LIMITS = {
    'EUR': 5000,
    'USD': 5500,
    'MGA': 24000000
}
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
            
            wallet = Wallet.objects.create(user=request.user, balance=Money(0, 'EUR'))
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
                    amount = Money(trans.amount, 'EUR')
                    wallet.deposit(amount)
                    
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
    def create_withdrawal(self, request):
        """
        Crée une demande de retrait
        """
        try:
            serializer = WithdrawalSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            amount = serializer.validated_data.get('amount')
            currency = serializer.validated_data.get('currency', 'EUR')
            
            # Vérifier la limite de retrait
            limit = WITHDRAWAL_LIMITS.get(currency, WITHDRAWAL_LIMITS['EUR'])
            if amount > limit:
                return Response({
                    "detail": f"Le montant dépasse la limite de retrait ({limit} {currency})."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer le portefeuille
            try:
                wallet = Wallet.objects.get(user=request.user)
            except Wallet.DoesNotExist:
                return Response({"detail": "Portefeuille non trouvé."}, status=status.HTTP_404_NOT_FOUND)
            
            # Vérifier le solde
            if wallet.balance.amount < amount:
                return Response({"detail": "Solde insuffisant."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer un transfert Stripe (dans un système réel, vous utiliseriez Stripe Connect)
            # Pour cet exemple, nous simulons simplement le transfert
            transfer = {
                'id': f'tr_{timezone.now().timestamp()}',
                'amount': int(amount * 100),
                'currency': currency.lower(),
                'status': 'pending'
            }
            
            # Créer une transaction
            with transaction.atomic():
                trans = Transaction.objects.create(
                    user=request.user,
                    transaction_type='withdrawal',
                    amount=amount,
                    status='pending',
                    reference_id=transfer['id']
                )
                
                # Dans un système réel, vous ne déduiriez pas immédiatement le montant
                # Mais pour cet exemple, nous le faisons
                money_amount = Money(amount, currency)
                wallet.withdraw(money_amount)
                
                # Créer une transaction de portefeuille
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='withdraw',
                    amount=amount
                )
                
                return Response({
                    "status": "Demande de retrait créée avec succès.",
                    "transaction_id": trans.id,
                    "amount": amount,
                    "currency": currency,
                    "estimated_arrival": (timezone.now() + timezone.timedelta(days=3)).strftime('%Y-%m-%d')
                })
                
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_currency(self, request):
        """
        Change la devise du portefeuille
        """
        try:
            serializer = CurrencySerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            currency = serializer.validated_data.get('currency')
            
            # Vérifier que la devise est prise en charge
            supported_currencies = ['EUR', 'USD', 'MGA']
            if currency not in supported_currencies:
                return Response({
                    "detail": f"Devise non prise en charge. Les devises disponibles sont: {', '.join(supported_currencies)}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer le portefeuille
            try:
                wallet = Wallet.objects.get(user=request.user)
            except Wallet.DoesNotExist:
                return Response({"detail": "Portefeuille non trouvé."}, status=status.HTTP_404_NOT_FOUND)
            
            # Si la devise est déjà celle du portefeuille, ne rien faire
            if wallet.balance.currency.code == currency:
                return Response({"status": f"La devise est déjà en {currency}."})
            
            # Convertir le solde dans la nouvelle devise
            from .models import convert_currency
            new_balance = convert_currency(
                wallet.balance.amount, 
                from_currency=wallet.balance.currency.code, 
                to_currency=currency
            )
            
            # Mettre à jour le portefeuille
            wallet.balance.currency = currency
            wallet.balance.amount = new_balance
            wallet.save()
            
            return Response({
                "status": f"Devise changée avec succès en {currency}.",
                "new_balance": str(new_balance),
                "currency": currency
            })
                
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def withdrawal_limits(self, request):
        """
        Récupère les limites de retrait
        """
        return Response(WITHDRAWAL_LIMITS)

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
