from django.db import models
from django.utils.text import slugify
from users.models import User

class Sector(models.Model):
    """
    Secteurs d'activité pour les projets
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Project(models.Model):
    """
    Projets d'investissement
    """
    FUNDING_TYPE_CHOICES = (
        ('equity', 'Equity'),
        ('loan', 'Prêt'),
        ('grant', 'Subvention'),
        ('crowdfunding', 'Crowdfunding'),
        ('other', 'Autre'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Brouillon'),
        ('pending', 'En attente de validation'),
        ('active', 'Actif'),
        ('funded', 'Financé'),
        ('closed', 'Clôturé'),
        ('rejected', 'Rejeté'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    description = models.TextField()
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, related_name='projects')
    funding_type = models.CharField(max_length=20, choices=FUNDING_TYPE_CHOICES)
    amount_needed = models.DecimalField(max_digits=15, decimal_places=2)
    amount_raised = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    minimum_investment = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_boosted = models.BooleanField(default=False)
    boost_until = models.DateTimeField(null=True, blank=True)
    views_count = models.PositiveIntegerField(default=0)
    interests_count = models.PositiveIntegerField(default=0)
    participants_count = models.PositiveIntegerField(default=0)
    video_url = models.URLField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def funding_percentage(self):
        if self.amount_needed > 0:
            return (self.amount_raised / self.amount_needed) * 100
        return 0

class ProjectMedia(models.Model):
    """
    Images et documents associés à un projet
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='project_media/')
    file_type = models.CharField(max_length=10, choices=(
        ('image', 'Image'),
        ('pdf', 'PDF'),
        ('doc', 'Document'),
    ))
    title = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.file_type} pour {self.project.title}"

