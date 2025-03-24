from django.db import models
from users.models import User

class PaymentMethod(models.Model):
    """
    Méthodes de paiement enregistrées par les utilisateurs
    """
    METHOD_TYPES = (
        ('credit_card', 'Carte de crédit'),
        ('bank_transfer', 'Virement bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('paypal', 'PayPal'),
        ('other', 'Autre'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
    provider = models.CharField(max_length=50, blank=True)
    account_number = models.CharField(max_length=50, blank=True)  # Masqué pour la sécurité
    expiry_date = models.DateField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['user', 'method_type', 'account_number']]
    
    def __str__(self):
        return f"{self.method_type} de {self.user.username}"

class Invoice(models.Model):
    """
    Factures pour les paiements
    """
    STATUS_CHOICES = (
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('paid', 'Payée'),
        ('cancelled', 'Annulée'),
        ('overdue', 'En retard'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    issue_date = models.DateField()
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"Facture {self.invoice_number} pour {self.user.username}"

