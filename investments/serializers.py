# investments/serializers.py
from rest_framework import serializers
from .models import Investment, Transaction
from projects.serializers import ProjectListSerializer
from users.serializers import UserProfileSerializer
from django.db import transaction as db_transaction

class TransactionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les transactions
    """
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'transaction_type', 'amount', 'status',
            'reference_id', 'created_at', 'completed_at', 'description'
        ]
        read_only_fields = [
            'id', 'user', 'transaction_type', 'reference_id',
            'created_at', 'completed_at'
        ]

class InvestmentSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les investissements
    """
    investor = UserProfileSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Investment
        fields = [
            'id', 'investor', 'project', 'amount', 'commission_amount',
            'status', 'transaction_id', 'created_at', 'completed_at',
            'notes', 'transactions'
        ]
        read_only_fields = [
            'id', 'investor', 'commission_amount', 'status', 'transaction_id',
            'created_at', 'completed_at', 'transactions'
        ]

class InvestmentCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'investissements
    """
    project_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Investment
        fields = ['project_id', 'amount', 'notes']
    
    def validate_amount(self, value):
        """
        Vérifie que le montant est positif et supérieur au minimum requis
        """
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        
        project_id = self.initial_data.get('project_id')
        from projects.models import Project
        
        try:
            project = Project.objects.get(id=project_id)
            if value < project.minimum_investment:
                raise serializers.ValidationError(
                    f"Le montant minimum d'investissement pour ce projet est de {project.minimum_investment}."
                )
        except Project.DoesNotExist:
            pass  # La validation du projet_id sera gérée ailleurs
        
        return value
    
    def validate_project_id(self, value):
        """
        Vérifie que le projet existe et est actif
        """
        from projects.models import Project
        
        try:
            project = Project.objects.get(id=value)
            if project.status != 'active':
                raise serializers.ValidationError("Ce projet n'est pas ouvert aux investissements.")
            
            # Vérifier si le projet a atteint son objectif
            if project.amount_raised >= project.amount_needed:
                raise serializers.ValidationError("Ce projet a déjà atteint son objectif de financement.")
            
            # Vérifier si l'utilisateur est le propriétaire du projet
            if project.owner == self.context['request'].user:
                raise serializers.ValidationError("Vous ne pouvez pas investir dans votre propre projet.")
            
            return value
        except Project.DoesNotExist:
            raise serializers.ValidationError("Le projet spécifié n'existe pas.")
    
    @db_transaction.atomic
    def create(self, validated_data):
        """
        Crée un nouvel investissement et les transactions associées
        """
        from projects.models import Project
        from notifications.utils import create_investment_notification
        
        project_id = validated_data.pop('project_id')
        project = Project.objects.get(id=project_id)
        investor = self.context['request'].user
        amount = validated_data.get('amount')
        
        # Calculer la commission (10% selon le cahier des charges)
        commission_rate = 0.10
        commission_amount = amount * commission_rate
        
        # Créer l'investissement
        investment = Investment.objects.create(
            investor=investor,
            project=project,
            amount=amount,
            commission_amount=commission_amount,
            status='pending',
            **validated_data
        )
        
        # Créer les transactions associées
        # 1. Transaction d'investissement (débit du compte de l'investisseur)
        investment_transaction = Transaction.objects.create(
            user=investor,
            transaction_type='investment',
            amount=amount,
            status='pending',
            investment=investment,
            description=f"Investissement dans le projet '{project.title}'"
        )
        
        # 2. Transaction de commission (débit du compte de l'investisseur)
        commission_transaction = Transaction.objects.create(
            user=investor,
            transaction_type='commission',
            amount=commission_amount,
            status='pending',
            investment=investment,
            description=f"Commission pour l'investissement dans le projet '{project.title}'"
        )
        
        # Mettre à jour le montant collecté du projet
        # Note: Nous ne l'ajoutons pas immédiatement car l'investissement est en attente
        # Cela sera fait lors de la confirmation de l'investissement
        
        # Créer une notification pour le propriétaire du projet
        create_investment_notification(
            project_owner=project.owner,
            investor=investor,
            project=project,
            investment=investment
        )
        
        return investment

class DepositSerializer(serializers.Serializer):
    """
    Sérialiseur pour les dépôts
    """
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    payment_method = serializers.CharField(required=True)
    
    def validate_amount(self, value):
        """
        Vérifie que le montant est positif
        """
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value
    
    @db_transaction.atomic
    def create(self, validated_data):
        """
        Crée une transaction de dépôt
        """
        user = self.context['request'].user
        amount = validated_data.get('amount')
        payment_method = validated_data.get('payment_method')
        
        # Créer la transaction de dépôt
        transaction = Transaction.objects.create(
            user=user,
            transaction_type='deposit',
            amount=amount,
            status='pending',
            description=f"Dépôt via {payment_method}"
        )
        
        # Ici, vous intégreriez avec un système de paiement réel
        # Pour cet exemple, nous simulons une transaction réussie
        
        return transaction

class WithdrawalSerializer(serializers.Serializer):
    """
    Sérialiseur pour les retraits
    """
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    bank_details = serializers.CharField(required=True)
    
    def validate_amount(self, value):
        """
        Vérifie que le montant est positif et que l'utilisateur a suffisamment de fonds
        """
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        
        user = self.context['request'].user
        
        # Calculer le solde de l'utilisateur
        from django.db.models import Sum
        
        deposits = Transaction.objects.filter(
            user=user,
            transaction_type='deposit',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        withdrawals = Transaction.objects.filter(
            user=user,
            transaction_type='withdrawal',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        investments = Transaction.objects.filter(
            user=user,
            transaction_type='investment',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        commissions = Transaction.objects.filter(
            user=user,
            transaction_type='commission',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        balance = deposits - withdrawals - investments - commissions
        
        if value > balance:
            raise serializers.ValidationError("Solde insuffisant pour effectuer ce retrait.")
        
        return value
    
    @db_transaction.atomic
    def create(self, validated_data):
        """
        Crée une transaction de retrait
        """
        user = self.context['request'].user
        amount = validated_data.get('amount')
        bank_details = validated_data.get('bank_details')
        
        # Créer la transaction de retrait
        transaction = Transaction.objects.create(
            user=user,
            transaction_type='withdrawal',
            amount=amount,
            status='pending',
            description=f"Retrait vers {bank_details}"
        )
        
        # Ici, vous intégreriez avec un système de paiement réel
        # Pour cet exemple, nous simulons une transaction en attente
        
        return transaction