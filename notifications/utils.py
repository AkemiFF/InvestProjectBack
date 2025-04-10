# notifications/utils.py
from .models import Notification


def create_notification(recipient, notification_type, title, message, related_object_id=None, related_object_type=None):
    """
    Crée une nouvelle notification
    
    Args:
        recipient: L'utilisateur destinataire de la notification
        notification_type: Le type de notification (voir les choix dans le modèle)
        title: Le titre de la notification
        message: Le message de la notification
        related_object_id: L'ID de l'objet lié (optionnel)
        related_object_type: Le type de l'objet lié (optionnel)
    
    Returns:
        La notification créée
    """
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        related_object_id=related_object_id,
        related_object_type=related_object_type
    )
    
    return notification

def create_comment_notification(project_owner, commenter, project, comment):
    """
    Crée une notification pour un nouveau commentaire
    """
    return create_notification(
        recipient=project_owner,
        notification_type='comment',
        title='Nouveau commentaire',
        message=f"{commenter.first_name} {commenter.last_name} a commenté votre projet '{project.title}'",
        related_object_id=comment.id,
        related_object_type='comment'
    )

def create_reply_notification(comment_author, replier, project, reply):
    """
    Crée une notification pour une réponse à un commentaire
    """
    return create_notification(
        recipient=comment_author,
        notification_type='reply',
        title='Réponse à votre commentaire',
        message=f"{replier.first_name} {replier.last_name} a répondu à votre commentaire sur le projet '{project.title}'",
        related_object_id=reply.id,
        related_object_type='comment'
    )

def create_investment_notification(project_owner, investor, project, investment):
    """
    Crée une notification pour un nouvel investissement
    """
    return create_notification(
        recipient=project_owner,
        notification_type='investment',
        title='Nouvel investissement',
        message=f"{investor.first_name} {investor.last_name} a investi {investment.amount} dans votre projet '{project.title}'",
        related_object_id=investment.id,
        related_object_type='investment'
    )

def create_project_update_notification(investor, project_owner, project):
    """
    Crée une notification pour une mise à jour de projet
    """
    return create_notification(
        recipient=investor,
        notification_type='project_update',
        title='Mise à jour de projet',
        message=f"{project_owner.first_name} {project_owner.last_name} a mis à jour le projet '{project.title}'",
        related_object_id=project.id,
        related_object_type='project'
    )

def create_system_notification(recipient, title, message,related_object):
    """
    Crée une notification système
    """
    return create_notification(
        recipient=recipient,
        notification_type='system',
        title=title,
        message=message,
        related_object_type=related_object
    )