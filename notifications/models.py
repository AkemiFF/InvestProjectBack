from django.db import models
from users.models import User

class Notification(models.Model):
    """
    Notifications pour les utilisateurs
    """
    NOTIFICATION_TYPES = (
        ('comment', 'Nouveau commentaire'),
        ('reply', 'Réponse à un commentaire'),
        ('message', 'Nouveau message'),
        ('investment', 'Nouvel investissement'),
        ('project_update', 'Mise à jour de projet'),
        ('system', 'Notification système'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} pour {self.recipient.username}"

