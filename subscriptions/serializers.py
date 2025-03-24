# subscriptions/serializers.py
from rest_framework import serializers
from .models import SubscriptionPlan, Subscription, ProjectBoost
from users.serializers import UserProfileSerializer
from projects.serializers import ProjectListSerializer
from django.db import transaction
from django.utils import timezone
import datetime

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les plans d'abonnement
    """
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'plan_type', 'price', 'duration_days',
            'description', 'features', 'is_active'
        ]

class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les abonnements
    """
    user = UserProfileSerializer(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)
    days_left = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'status', 'start_date', 'end_date',
            'auto_renew', 'created_at', 'transaction_id', 'days_left'
        ]
        read_only_fields = [
            'id', 'user', 'plan', 'status', 'start_date', 'end_date',
            'created_at', 'transaction_id'
        ]
    
    def get_days_left(self, obj):
        """
        Calcule le nombre de jours restants pour l'abonnement
        """
        if obj.status != 'active' or not obj.end_date:
            return 0
        
        today = timezone.now().date()
        if obj.end_date < today:
            return 0
        
        delta = obj.end_date - today
        return delta.days

class SubscriptionCreateSerializer(serializers.Serializer):
    """
    Sérialiseur pour la création d'abonnements
    """
    plan_id = serializers.IntegerField(required=True)
    auto_renew = serializers.BooleanField(default=False)
    
    def validate_plan_id(self, value):
        """
        Vérifie que le plan existe et est actif
        """
        try:
            plan = SubscriptionPlan.objects.get(id=value)
            if not plan.is_active:
                raise serializers.ValidationError("Ce plan d'abonnement n'est pas disponible.")
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Le plan spécifié n'existe pas.")
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Crée un nouvel abonnement
        """
        from notifications.utils import create_system_notification
        
        user = self.context['request'].user
        plan_id = validated_data.get('plan_id')
        auto_renew = validated_data.get('auto_renew', False)
        
        plan = SubscriptionPlan.objects.get(id=plan_id)
        
        # Vérifier si l'utilisateur a déjà un abonnement actif
        active_subscription = Subscription.objects.filter(
            user=user,
            status='active',
            end_date__gte=timezone.now().date()
        ).first()
        
        if active_subscription:
            # Si l'abonnement actif est du même type, prolonger la durée
            if active_subscription.plan.plan_type == plan.plan_type:
                active_subscription.end_date = active_subscription.end_date + datetime.timedelta(days=plan.duration_days)
                active_subscription.auto_renew = auto_renew
                active_subscription.save(update_fields=['end_date', 'auto_renew'])
                
                # Créer une notification
                create_system_notification(
                    recipient=user,
                    title="Abonnement prolongé",
                    message=f"Votre abonnement {plan.name} a été prolongé jusqu'au {active_subscription.end_date.strftime('%d/%m/%Y')}."
                )
                
                return active_subscription
            else:
                # Si l'abonnement est d'un type différent, désactiver l'ancien et en créer un nouveau
                active_subscription.status = 'cancelled'
                active_subscription.save(update_fields=['status'])
        
        # Créer un nouvel abonnement
        start_date = timezone.now()
        end_date = start_date + datetime.timedelta(days=plan.duration_days)
        
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status='pending',  # Sera mis à jour après le paiement
            start_date=start_date,
            end_date=end_date,
            auto_renew=auto_renew
        )
        
        # Dans un système réel, ici vous intégreriez avec un système de paiement
        # Pour cet exemple, nous simulons un paiement réussi
        
        # Simuler un ID de transaction
        import uuid
        transaction_id = str(uuid.uuid4())
        
        # Mettre à jour l'abonnement
        subscription.status = 'active'
        subscription.transaction_id = transaction_id
        subscription.save(update_fields=['status', 'transaction_id'])
        
        # Créer une notification
        create_system_notification(
            recipient=user,
            title="Abonnement activé",
            message=f"Votre abonnement {plan.name} a été activé et est valable jusqu'au {end_date.strftime('%d/%m/%Y')}."
        )
        
        return subscription

class ProjectBoostSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les boosts de projets
    """
    project = ProjectListSerializer(read_only=True)
    
    class Meta:
        model = ProjectBoost
        fields = [
            'id', 'project', 'start_date', 'end_date', 'days',
            'amount_paid', 'transaction_id', 'is_active'
        ]
        read_only_fields = [
            'id', 'project', 'start_date', 'end_date', 'amount_paid',
            'transaction_id', 'is_active'
        ]

class ProjectBoostCreateSerializer(serializers.Serializer):
    """
    Sérialiseur pour la création de boosts de projets
    """
    project_id = serializers.IntegerField(required=True)
    days = serializers.IntegerField(required=True, min_value=1)
    
    def validate_project_id(self, value):
        """
        Vérifie que le projet existe et appartient à l'utilisateur
        """
        from projects.models import Project
        
        try:
            project = Project.objects.get(id=value)
            if project.owner != self.context['request'].user:
                raise serializers.ValidationError("Vous ne pouvez booster que vos propres projets.")
            return value
        except Project.DoesNotExist:
            raise serializers.ValidationError("Le projet spécifié n'existe pas.")
    
    def validate_days(self, value):
        """
        Vérifie que le nombre de jours est valide
        """
        if value <= 0:
            raise serializers.ValidationError("Le nombre de jours doit être positif.")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Crée un nouveau boost de projet
        """
        from projects.models import Project
        from notifications.utils import create_system_notification
        
        user = self.context['request'].user
        project_id = validated_data.get('project_id')
        days = validated_data.get('days')
        
        project = Project.objects.get(id=project_id)
        
        # Calculer le montant à payer (5000 MGA par jour selon le cahier des charges)
        amount_per_day = 5000
        amount_paid = days * amount_per_day
        
        # Dates de début et de fin
        start_date = timezone.now()
        end_date = start_date + datetime.timedelta(days=days)
        
        # Créer le boost
        boost = ProjectBoost.objects.create(
            project=project,
            start_date=start_date,
            end_date=end_date,
            days=days,
            amount_paid=amount_paid,
            is_active=True
        )
        
        # Dans un système réel, ici vous intégreriez avec un système de paiement
        # Pour cet exemple, nous simulons un paiement réussi
        
        # Simuler un ID de transaction
        import uuid
        transaction_id = str(uuid.uuid4())
        boost.transaction_id = transaction_id
        boost.save(update_fields=['transaction_id'])
        
        # Mettre à jour le statut de boost du projet
        project.is_boosted = True
        project.save(update_fields=['is_boosted'])
        
        # Créer une notification
        create_system_notification(
            recipient=user,
            title="Projet boosté",
            message=f"Votre projet '{project.title}' a été boosté pour {days} jours, jusqu'au {end_date.strftime('%d/%m/%Y')}."
        )
        
        return boost