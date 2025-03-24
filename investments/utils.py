# investments/utils.py
from django.db.models import Sum, F, Q
from .models import Transaction

def calculate_user_balance(user):
    """
    Calcule le solde d'un utilisateur
    """
    # Somme des dépôts complétés
    deposits = Transaction.objects.filter(
        user=user,
        transaction_type='deposit',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Somme des retraits complétés
    withdrawals = Transaction.objects.filter(
        user=user,
        transaction_type='withdrawal',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Somme des investissements complétés
    investments = Transaction.objects.filter(
        user=user,
        transaction_type='investment',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Somme des commissions complétées
    commissions = Transaction.objects.filter(
        user=user,
        transaction_type='commission',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calcul du solde
    balance = deposits - withdrawals - investments - commissions
    
    return balance

def update_project_amount_raised(project):
    """
    Met à jour le montant collecté d'un projet
    """
    from .models import Investment
    
    # Somme des investissements complétés pour ce projet
    total_invested = Investment.objects.filter(
        project=project,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Mise à jour du montant collecté
    project.amount_raised = total_invested
    project.save(update_fields=['amount_raised'])
    
    return project

def update_user_investment_stats(user):
    """
    Met à jour les statistiques d'investissement d'un utilisateur
    """
    from .models import Investment
    
    # Nombre de projets soutenus
    projects_supported = Investment.objects.filter(
        investor=user,
        status='completed'
    ).values('project').distinct().count()
    
    # Montant total investi
    total_invested = Investment.objects.filter(
        investor=user,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Mise à jour du profil investisseur
    if hasattr(user, 'investor_profile'):
        user.investor_profile.projects_supported = projects_supported
        user.investor_profile.total_invested = total_invested
        user.investor_profile.balance = calculate_user_balance(user)
        user.investor_profile.save(update_fields=['projects_supported', 'total_invested', 'balance'])
    
    return user

def update_project_owner_stats(user):
    """
    Met à jour les statistiques du porteur de projet
    """
    from projects.models import Project
    
    # Nombre de campagnes actives
    active_campaigns = Project.objects.filter(
        owner=user,
        status='active'
    ).count()
    
    # Nombre de projets financés
    funded_projects = Project.objects.filter(
        owner=user,
        status='completed'
    ).count()
    
    # Mise à jour du profil porteur de projet
    if hasattr(user, 'project_owner_profile'):
        user.project_owner_profile.active_campaigns = active_campaigns
        user.project_owner_profile.funded_projects = funded_projects
        user.project_owner_profile.balance = calculate_user_balance(user)
        user.project_owner_profile.save(update_fields=['active_campaigns', 'funded_projects', 'balance'])
    
    return user