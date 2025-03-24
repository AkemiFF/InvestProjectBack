# payments/serializers.py
from rest_framework import serializers
from .models import PaymentMethod, Invoice
from users.serializers import UserProfileSerializer
from django.db import transaction
from django.utils import timezone
import datetime
import uuid

class PaymentMethodSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les méthodes de paiement
    """
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'user', 'method_type', 'provider', 'account_number',
            'expiry_date', 'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def to_representation(self, instance):
        """
        Masque partiellement le numéro de compte pour des raisons de sécurité
        """
        ret = super().to_representation(instance)
        if ret['account_number'] and len(ret['account_number']) > 4:
            # Masquer tous les caractères sauf les 4 derniers
            ret['account_number'] = '*' * (len(ret['account_number']) - 4) + ret['account_number'][-4:]
        return ret

class PaymentMethodCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création de méthodes de paiement
    """
    class Meta:
        model = PaymentMethod
        fields = [
            'method_type', 'provider', 'account_number',
            'expiry_date', 'is_default'
        ]
    
    def validate_expiry_date(self, value):
        """
        Vérifie que la date d'expiration est dans le futur
        """
        if value and value < timezone.now().date():
            raise serializers.ValidationError("La date d'expiration doit être dans le futur.")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Crée une nouvelle méthode de paiement
        """
        user = self.context['request'].user
        is_default = validated_data.get('is_default', False)
        
        # Si cette méthode est définie comme par défaut, désactiver les autres méthodes par défaut
        if is_default:
            PaymentMethod.objects.filter(user=user, is_default=True).update(is_default=False)
        
        # Si c'est la première méthode de paiement de l'utilisateur, la définir comme par défaut
        elif not PaymentMethod.objects.filter(user=user).exists():
            validated_data['is_default'] = True
        
        # Créer la méthode de paiement
        payment_method = PaymentMethod.objects.create(
            user=user,
            **validated_data
        )
        
        return payment_method

class InvoiceSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les factures
    """
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'user', 'invoice_number', 'amount', 'description',
            'status', 'issue_date', 'due_date', 'paid_date',
            'related_object_id', 'related_object_type'
        ]
        read_only_fields = [
            'id', 'user', 'invoice_number', 'amount', 'description',
            'status', 'issue_date', 'due_date', 'paid_date',
            'related_object_id', 'related_object_type'
        ]

class PaymentProcessSerializer(serializers.Serializer):
    """
    Sérialiseur pour le traitement des paiements
    """
    payment_method_id = serializers.IntegerField(required=True)
    invoice_id = serializers.IntegerField(required=True)
    
    def validate_payment_method_id(self, value):
        """
        Vérifie que la méthode de paiement existe et appartient à l'utilisateur
        """
        try:
            payment_method = PaymentMethod.objects.get(id=value)
            if payment_method.user != self.context['request'].user:
                raise serializers.ValidationError("Cette méthode de paiement ne vous appartient pas.")
            
            # Vérifier que la méthode de paiement n'est pas expirée
            if payment_method.expiry_date and payment_method.expiry_date < timezone.now().date():
                raise serializers.ValidationError("Cette méthode de paiement est expirée.")
            
            return value
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("La méthode de paiement spécifiée n'existe pas.")
    
    def validate_invoice_id(self, value):
        """
        Vérifie que la facture existe et appartient à l'utilisateur
        """
        try:
            invoice = Invoice.objects.get(id=value)
            if invoice.user != self.context['request'].user:
                raise serializers.ValidationError("Cette facture ne vous appartient pas.")
            
            # Vérifier que la facture n'est pas déjà payée
            if invoice.status == 'paid':
                raise serializers.ValidationError("Cette facture est déjà payée.")
            
            # Vérifier que la facture n'est pas annulée
            if invoice.status == 'cancelled':
                raise serializers.ValidationError("Cette facture a été annulée.")
            
            return value
        except Invoice.DoesNotExist:
            raise serializers.ValidationError("La facture spécifiée n'existe pas.")
    
    @transaction.atomic
    def save(self):
        """
        Traite le paiement
        """
        from notifications.utils import create_system_notification
        
        payment_method_id = self.validated_data.get('payment_method_id')
        invoice_id = self.validated_data.get('invoice_id')
        
        payment_method = PaymentMethod.objects.get(id=payment_method_id)
        invoice = Invoice.objects.get(id=invoice_id)
        
        # Dans un système réel, ici vous intégreriez avec un système de paiement
        # Pour cet exemple, nous simulons un paiement réussi
        
        # Mettre à jour la facture
        invoice.status = 'paid'
        invoice.paid_date = timezone.now().date()
        invoice.save(update_fields=['status', 'paid_date'])
        
        # Créer une notification
        create_system_notification(
            recipient=self.context['request'].user,
            title="Paiement effectué",
            message=f"Votre paiement de {invoice.amount} MGA pour la facture {invoice.invoice_number} a été effectué avec succès."
        )
        
        # Mettre à jour l'objet lié si nécessaire
        if invoice.related_object_type == 'subscription':
            from subscriptions.models import Subscription
            try:
                subscription = Subscription.objects.get(id=invoice.related_object_id)
                subscription.status = 'active'
                subscription.save(update_fields=['status'])
            except Subscription.DoesNotExist:
                pass
        elif invoice.related_object_type == 'project_boost':
            from subscriptions.models import ProjectBoost
            try:
                boost = ProjectBoost.objects.get(id=invoice.related_object_id)
                boost.is_active = True
                boost.save(update_fields=['is_active'])
                
                # Mettre à jour le statut du projet
                boost.project.is_boosted = True
                boost.project.save(update_fields=['is_boosted'])
            except ProjectBoost.DoesNotExist:
                pass
        
        return invoice

class TransactionSerializer(serializers.Serializer):
    """
    Sérialiseur pour les transactions (non stockées en base de données)
    """
    id = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(read_only=True, max_digits=15, decimal_places=2)
    date = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    invoice_id = serializers.IntegerField(read_only=True, source='invoice.id')
    invoice_number = serializers.CharField(read_only=True, source='invoice.invoice_number')
    payment_method = serializers.CharField(read_only=True)