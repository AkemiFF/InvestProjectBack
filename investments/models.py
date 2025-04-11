from django.db import models
from projects.models import Project
from users.models import User


class Investment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('wallet', 'Portefeuille'),
        ('card', 'Carte'),
        ('bank', 'Virement bancaire'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='investments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    payment_session_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.project.title} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Si le statut passe à 'completed', mettre à jour le montant collecté du projet
        if self.status == 'completed' and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
            
            # Mettre à jour le montant collecté du projet
            self.project.amount_raised += self.amount
            self.project.save()
        
        super().save(*args, **kwargs)


class Transaction(models.Model):
    """
    Transactions financières
    """
    TRANSACTION_TYPES = (
        ('deposit', 'Dépôt'),
        ('withdrawal', 'Retrait'),
        ('investment', 'Investissement'),
        ('commission', 'Commission'),
        ('refund', 'Remboursement'),
        ('subscription', 'Abonnement'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference_id = models.CharField(max_length=100, blank=True)
    investment = models.ForeignKey(Investment, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.transaction_type} de {self.amount} pour {self.user.username}"

