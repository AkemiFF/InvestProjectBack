from django.db import models
from users.models import User

class AdminLog(models.Model):
    """
    Journal des actions administratives
    """
    ACTION_TYPES = (
        ('user_management', 'Gestion utilisateur'),
        ('project_validation', 'Validation de projet'),
        ('comment_moderation', 'Modération de commentaire'),
        ('payment_management', 'Gestion de paiement'),
        ('system_config', 'Configuration système'),
        ('other', 'Autre'),
    )
    
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_logs')
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.action_type} par {self.admin_user.username}"

class SystemSetting(models.Model):
    """
    Paramètres système pour la plateforme
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_settings')
    
    def __str__(self):
        return self.key

class Statistic(models.Model):
    """
    Statistiques de la plateforme
    """
    STAT_TYPES = (
        ('users', 'Utilisateurs'),
        ('projects', 'Projets'),
        ('investments', 'Investissements'),
        ('revenue', 'Revenus'),
        ('visits', 'Visites'),
        ('other', 'Autre'),
    )
    
    stat_type = models.CharField(max_length=20, choices=STAT_TYPES)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = [['stat_type', 'date']]
    
    def __str__(self):
        return f"{self.stat_type} - {self.date}"

