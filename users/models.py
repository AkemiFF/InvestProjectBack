from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé avec champs supplémentaires
    """
    USER_TYPE_CHOICES = (
        ('investor', 'Investisseur'),
        ('project_owner', 'Porteur de projet'),
        ('admin', 'Administrateur'),
    )
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    email_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    biography = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    currency = models.CharField(max_length=10, choices=[('Ariary', 'Ariary'), ('Euro', 'Euro'),('Dollars', 'Dollars')], default='Euro')
    
    
    # Champs pour l'authentification sociale
    google_id = models.CharField(max_length=100, blank=True, null=True)
    linkedin_id = models.CharField(max_length=100, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def is_investor(self):
            return self.user_type == 'investor'
        
    def is_project_owner(self):
        return self.user_type == 'project_owner'
    
    class Meta:
        
        verbose_name = _('user')
        verbose_name_plural = _('users')

class InvestorProfile(models.Model):
    """
    Profil spécifique pour les investisseurs
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='investor_profile')
    investment_domain = models.CharField(max_length=100, blank=True)
    total_invested = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    projects_supported = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Profil investisseur de {self.user.username}"

class ProjectOwnerProfile(models.Model):
    """
    Profil spécifique pour les porteurs de projet
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='project_owner_profile')
    active_campaigns = models.PositiveIntegerField(default=0)
    funded_projects = models.PositiveIntegerField(default=0)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Profil porteur de projet de {self.user.username}"

class Favorite(models.Model):
    """
    Projets ou porteurs de projet favoris
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True, blank=True)
    project_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorited_by', null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['user', 'project'], ['user', 'project_owner']]



class RegistrationRequest(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email}: {self.code}"

    class Meta:
        verbose_name = "Registration Request"
        verbose_name_plural = "Registration Requests"

    
    def is_expired(self):
        expiration_time = self.created_at + timezone.timedelta(minutes=15)
        return timezone.now() > expiration_time
    