# admin_dashboard/utils.py
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncDate, TruncMonth
from users.models import User
from projects.models import Project
from investments.models import Investment
from comments.models import Comment
from .models import AdminLog, Statistic
import datetime

def log_admin_action(admin_user, action_type, description, related_object=None, ip_address=None):
    """
    Enregistre une action administrative dans le journal
    """
    log = AdminLog(
        admin_user=admin_user,
        action_type=action_type,
        description=description,
        ip_address=ip_address
    )
    
    if related_object:
        log.related_object_id = related_object.id
        log.related_object_type = related_object.__class__.__name__.lower()
    
    log.save()
    return log

def get_dashboard_metrics():
    """
    Récupère les métriques pour le tableau de bord administratif
    """
    today = timezone.now().date()
    yesterday = today - datetime.timedelta(days=1)
    last_week = today - datetime.timedelta(days=7)
    last_month = today - datetime.timedelta(days=30)
    
    # Utilisateurs
    total_users = User.objects.count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_users_yesterday = User.objects.filter(date_joined__date=yesterday).count()
    new_users_last_week = User.objects.filter(date_joined__date__gte=last_week).count()
    new_users_last_month = User.objects.filter(date_joined__date__gte=last_month).count()
    
    # Projets
    total_projects = Project.objects.count()
    new_projects_today = Project.objects.filter(created_at__date=today).count()
    pending_projects = Project.objects.filter(status='pending').count()
    
    # Investissements
    total_investments = Investment.objects.count()
    total_investment_amount = Investment.objects.filter(status='confirmed').aggregate(Sum('amount'))['amount__sum'] or 0
    new_investments_today = Investment.objects.filter(created_at__date=today).count()
    
    # Commentaires
    total_comments = Comment.objects.count()
    new_comments_today = Comment.objects.filter(created_at__date=today).count()
    reported_comments = Comment.objects.filter(is_reported=True, is_moderated=False).count()
    
    # Revenus (à adapter selon votre modèle de revenus)
    from payments.models import Invoice
    total_revenue = Invoice.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    revenue_today = Invoice.objects.filter(paid_date=today, status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    revenue_yesterday = Invoice.objects.filter(paid_date=yesterday, status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    revenue_last_week = Invoice.objects.filter(paid_date__gte=last_week, status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    revenue_last_month = Invoice.objects.filter(paid_date__gte=last_month, status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    
    return {
        'users': {
            'total': total_users,
            'new_today': new_users_today,
            'new_yesterday': new_users_yesterday,
            'new_last_week': new_users_last_week,
            'new_last_month': new_users_last_month,
            'growth_rate': calculate_growth_rate(new_users_yesterday, new_users_today)
        },
        'projects': {
            'total': total_projects,
            'new_today': new_projects_today,
            'pending': pending_projects
        },
        'investments': {
            'total': total_investments,
            'total_amount': total_investment_amount,
            'new_today': new_investments_today
        },
        'comments': {
            'total': total_comments,
            'new_today': new_comments_today,
            'reported': reported_comments
        },
        'revenue': {
            'total': total_revenue,
            'today': revenue_today,
            'yesterday': revenue_yesterday,
            'last_week': revenue_last_week,
            'last_month': revenue_last_month,
            'growth_rate': calculate_growth_rate(revenue_yesterday, revenue_today)
        }
    }

def calculate_growth_rate(previous, current):
    """
    Calcule le taux de croissance entre deux valeurs
    """
    if previous == 0:
        return 100 if current > 0 else 0
    
    return ((current - previous) / previous) * 100

def get_user_growth_data(period='month', limit=12):
    """
    Récupère les données de croissance des utilisateurs pour une période donnée
    """
    today = timezone.now().date()
    
    if period == 'day':
        start_date = today - datetime.timedelta(days=limit)
        trunc_function = TruncDate('date_joined')
        date_format = '%Y-%m-%d'
    elif period == 'month':
        start_date = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        start_date = start_date.replace(day=1) - datetime.timedelta(days=limit * 30)
        trunc_function = TruncMonth('date_joined')
        date_format = '%Y-%m'
    else:
        raise ValueError("La période doit être 'day' ou 'month'")
    
    user_data = User.objects.filter(
        date_joined__date__gte=start_date
    ).annotate(
        period=trunc_function
    ).values(
        'period'
    ).annotate(
        count=Count('id')
    ).order_by('period')
    
    result = []
    for data in user_data:
        result.append({
            'period': data['period'].strftime(date_format),
            'count': data['count']
        })
    
    return result

def get_revenue_data(period='month', limit=12):
    """
    Récupère les données de revenus pour une période donnée
    """
    from payments.models import Invoice
    
    today = timezone.now().date()
    
    if period == 'day':
        start_date = today - datetime.timedelta(days=limit)
        trunc_function = TruncDate('paid_date')
        date_format = '%Y-%m-%d'
    elif period == 'month':
        start_date = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        start_date = start_date.replace(day=1) - datetime.timedelta(days=limit * 30)
        trunc_function = TruncMonth('paid_date')
        date_format = '%Y-%m'
    else:
        raise ValueError("La période doit être 'day' ou 'month'")
    
    revenue_data = Invoice.objects.filter(
        status='paid',
        paid_date__gte=start_date
    ).annotate(
        period=trunc_function
    ).values(
        'period'
    ).annotate(
        total=Sum('amount')
    ).order_by('period')
    
    result = []
    for data in revenue_data:
        result.append({
            'period': data['period'].strftime(date_format),
            'amount': data['total']
        })
    
    return result

def update_daily_statistics():
    """
    Met à jour les statistiques quotidiennes
    """
    today = timezone.now().date()
    
    # Utilisateurs
    total_users = User.objects.count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    
    # Projets
    total_projects = Project.objects.count()
    new_projects_today = Project.objects.filter(created_at__date=today).count()
    
    # Investissements
    total_investment_amount = Investment.objects.filter(status='confirmed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Revenus
    from payments.models import Invoice
    revenue_today = Invoice.objects.filter(paid_date=today, status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Visites (à adapter selon votre système de suivi des visites)
    visits_today = 0  # À remplacer par votre logique de suivi des visites
    
    # Mettre à jour ou créer les statistiques
    stats = [
        ('users', total_users),
        ('projects', total_projects),
        ('investments', total_investment_amount),
        ('revenue', revenue_today),
        ('visits', visits_today)
    ]
    
    for stat_type, value in stats:
        Statistic.objects.update_or_create(
            stat_type=stat_type,
            date=today,
            defaults={'value': value}
        )
    
    return True