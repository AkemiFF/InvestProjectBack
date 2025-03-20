from django.db import models
from users.models import User

class SubscriptionPlan(models.Model):
    """
    Plans d'abonnement disponibles
    """
    PLAN_TYPES = (
        ('basic', 'Basique'),
        ('premium_investor', 'Premium Investisseur'),
        ('premium_project_owner', 'Premium Porteur de projet'),
    )
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=30, choices=PLAN_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    description = models.TextField()
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Subscription(models.Model):
    """
    Abonnements des utilisateurs
    """
    STATUS_CHOICES = (
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé'),
        ('pending', 'En attente'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

class ProjectBoost(models.Model):
    """
    Boosts payants pour les projets
    """
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='boosts')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    days = models.PositiveIntegerField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Boost pour {self.project.title}"

