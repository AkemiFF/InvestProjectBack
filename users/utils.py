# users/utils.py
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

def send_verification_email(user):
    """
    Envoie un email de vérification à l'utilisateur
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    verification_link = f"{settings.FRONTEND_URL}/auth/verify-email?token={token}&uid={uid}"
    
    subject = "Vérification de votre adresse email"
    message = f"""
    Bonjour {user.first_name},
    
    Merci de vous être inscrit sur notre plateforme. Veuillez cliquer sur le lien ci-dessous pour vérifier votre adresse email:
    
    {verification_link}
    
    Ce lien est valable pendant 24 heures.
    
    Cordialement,
    L'équipe de la plateforme
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def send_password_reset_email(user):
    """
    Envoie un email de réinitialisation de mot de passe à l'utilisateur
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}&uid={uid}"
    
    subject = "Réinitialisation de votre mot de passe"
    message = f"""
    Bonjour {user.first_name},
    
    Vous avez demandé la réinitialisation de votre mot de passe. Veuillez cliquer sur le lien ci-dessous pour définir un nouveau mot de passe:
    
    {reset_link}
    
    Ce lien est valable pendant 24 heures.
    
    Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email.
    
    Cordialement,
    L'équipe de la plateforme
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def verify_token(uid, token):
    """
    Vérifie la validité d'un token et retourne l'utilisateur correspondant
    """
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
        
        if default_token_generator.check_token(user, token):
            return user
        return None
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None