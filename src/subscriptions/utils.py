# subscriptions/utils.py
from django.utils import timezone
from .models import Subscription, ProjectBoost

def check_subscription_status(user):
    """
    Vérifie si l'utilisateur a un abonnement actif et met à jour son statut si nécessaire
    """
    # Récupérer l'abonnement actif de l'utilisateur
    subscription = Subscription.objects.filter(
        user=user,
        status='active',
        end_date__gte=timezone.now().date()
    ).first()
    
    if not subscription:
        return None
    
    # Vérifier si l'abonnement est sur le point d'expirer
    today = timezone.now().date()
    days_left = (subscription.end_date - today).days
    
    # Si l'abonnement expire dans moins de 7 jours et que le renouvellement automatique est activé
    if days_left <= 7 and subscription.auto_renew:
        # Dans un système réel, ici vous initieriez le processus de renouvellement
        pass
    
    return subscription

def check_project_boost_status(project):
    """
    Vérifie si un projet a un boost actif et met à jour son statut si nécessaire
    """
    # Récupérer le boost actif du projet
    boost = ProjectBoost.objects.filter(
        project=project,
        is_active=True,
        end_date__gte=timezone.now()
    ).first()
    
    if not boost:
        # Si aucun boost actif n'est trouvé, mettre à jour le statut du projet
        if project.is_boosted:
            project.is_boosted = False
            project.save(update_fields=['is_boosted'])
        return None
    
    return boost

def get_user_subscription_type(user):
    """
    Récupère le type d'abonnement actif de l'utilisateur
    """
    subscription = check_subscription_status(user)
    
    if not subscription:
        return 'basic'  # Abonnement de base par défaut
    
    return subscription.plan.plan_type