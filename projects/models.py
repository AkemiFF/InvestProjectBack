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
    short_description = models.TextField(default="")
    description = models.TextField(default="")
    business_model = models.TextField(null=True, blank=True)
    market_analysis = models.TextField(null=True, blank=True)
    competitive_advantage = models.TextField(null=True, blank=True)
    use_of_funds = models.TextField(null=True, blank=True)
    financial_projections = models.TextField(null=True, blank=True)
    risks = models.TextField(null=True, blank=True)
    milestones = models.TextField(null=True, blank=True)
    equity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    maximum_investment = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    expected_return = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    return_timeline = models.CharField(max_length=100, null=True, blank=True)
    allow_partial_funding = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    location = models.CharField(max_length=255, null=True, blank=True)
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
            base_slug = slugify(self.title)
            unique_slug = base_slug
            num = 1
            while Project.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def funding_percentage(self):
        if self.amount_needed > 0:
            return (self.amount_raised / self.amount_needed) * 100
        return 0

class TeamMember(models.Model):
        """
        Membres de l'équipe du projet
        """
        project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_members')
        name = models.CharField(max_length=100)
        role = models.CharField(max_length=100)
        photo = models.ImageField(upload_to='team_photos/', blank=True, null=True)
        facebook_url = models.URLField(blank=True, null=True)
        
        def __str__(self):
            return f"{self.name} - {self.role}"

class ProjectUpdate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='update_project')
    date = models.DateField()
    title = models.CharField(max_length=255)
    content = models.TextField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.title}"



class ProjectMedia(models.Model):
    """
    Images et documents associés à un projet
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='media')
    cover = models.BooleanField(default=False)
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

