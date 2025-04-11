# admin_dashboard/serializers.py
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from users.serializers import UserProfileSerializer

from .models import AdminLog, Statistic, SystemSetting


class AdminLogSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les journaux d'administration
    """
    admin_user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = AdminLog
        fields = [
            'id', 'admin_user', 'action_type', 'description',
            'ip_address', 'created_at', 'related_object_id', 'related_object_type'
        ]
        read_only_fields = [
            'id', 'admin_user', 'created_at'
        ]

class SystemSettingSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les paramètres système
    """
    updated_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = SystemSetting
        fields = [
            'id', 'key', 'value', 'description',
            'is_public', 'updated_at', 'updated_by'
        ]
        read_only_fields = ['id', 'updated_at', 'updated_by']

class StatisticSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les statistiques
    """
    class Meta:
        model = Statistic
        fields = ['id', 'stat_type', 'value', 'date', 'description']
        read_only_fields = ['id']

class DashboardMetricsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les métriques du tableau de bord
    """
    users = serializers.DictField(read_only=True)
    projects = serializers.DictField(read_only=True)
    investments = serializers.DictField(read_only=True)
    comments = serializers.DictField(read_only=True)
    revenue = serializers.DictField(read_only=True)

class UserManagementSerializer(serializers.Serializer):
    """
    Sérialiseur pour la gestion des utilisateurs
    """
    user_id = serializers.IntegerField(required=True)
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'verify', 'make_admin', 'remove_admin'],
        required=True
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_user_id(self, value):
        """
        Vérifie que l'utilisateur existe
        """
        from users.models import User
        
        try:
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("L'utilisateur spécifié n'existe pas.")
    
    @transaction.atomic
    def save(self):
        """
        Exécute l'action sur l'utilisateur
        """
        from users.models import User

        from .utils import log_admin_action
        
        user_id = self.validated_data.get('user_id')
        action = self.validated_data.get('action')
        reason = self.validated_data.get('reason', '')
        user_type = self.validated_data.get('user_type', '')
        
        user = User.objects.get(id=user_id)
        admin_user = self.context['request'].user
        
        if action == 'activate':
            user.is_active = True
            user.save(update_fields=['is_active'])
            description = f"Activation du compte utilisateur {user.username}"
        
        elif action == 'deactivate':
            user.is_active = False
            user.save(update_fields=['is_active'])
            description = f"Désactivation du compte utilisateur {user.username}"
        
        elif action == 'verify':
            user.is_verified = True
            user.save(update_fields=['is_verified'])
            description = f"Vérification du compte utilisateur {user.username}"
        
        elif action == 'make_admin':
            user.is_staff = True
            user.save(update_fields=['is_staff'])
            description = f"Attribution des droits d'administrateur à {user.username}"
        
        elif action == 'update_role':
            user.is_staff = True
            user.save(user_type=user_type)
            description = f"Attribution des droits d'administrateur à {user.username}"
        
        elif action == 'remove_admin':
            user.is_staff = False
            user.save(update_fields=['is_staff'])
            description = f"Retrait des droits d'administrateur à {user.username}"
        
        # Ajouter la raison si elle est fournie
        if reason:
            description += f" - Raison: {reason}"
        
        # Enregistrer l'action dans le journal
        log_admin_action(
            admin_user=admin_user,
            action_type='user_management',
            description=description,
            related_object=user,
            ip_address=self.context['request'].META.get('REMOTE_ADDR')
        )
        
        return user

class ProjectManagementSerializer(serializers.Serializer):
    """
    Sérialiseur pour la gestion des projets
    """
    project_id = serializers.IntegerField(required=True)
    action = serializers.ChoiceField(
        choices=['active', 'reject', 'feature', 'unfeature', 'hide', 'unhide'],
        required=True
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_project_id(self, value):
        """
        Vérifie que le projet existe
        """
        from projects.models import Project
        
        try:
            Project.objects.get(id=value)
            return value
        except Project.DoesNotExist:
            raise serializers.ValidationError("Le projet spécifié n'existe pas.")
    
    @transaction.atomic
    def save(self):
        """
        Exécute l'action sur le projet
        """
        from notifications.utils import create_system_notification
        from projects.models import Project

        from .utils import log_admin_action
        
        project_id = self.validated_data.get('project_id')
        action = self.validated_data.get('action')
        reason = self.validated_data.get('reason', '')
        
        project = Project.objects.get(id=project_id)
        admin_user = self.context['request'].user
        
        if action == 'active':
            project.status = 'active'
            project.save(update_fields=['status'])
            description = f"Approbation du projet '{project.title}'"
            
            # Notifier le propriétaire du projet
            create_system_notification(
                recipient=project.owner,
                title="Projet approuvé",
                message=f"Votre projet '{project.title}' a été approuvé et est maintenant visible sur la plateforme.",
                related_object=project 
            )
        
        elif action == 'reject':
            project.status = 'rejected'
            project.save(update_fields=['status'])
            description = f"Rejet du projet '{project.title}'"
            
            # Notifier le propriétaire du projet
            create_system_notification(
                recipient=project.owner,
                title="Projet rejeté",
                message=f"Votre projet '{project.title}' a été rejeté. Raison: {reason or 'Non spécifiée'}",
                related_object=project 
            )
        
        elif action == 'feature':
            project.is_featured = True
            project.save(update_fields=['is_featured'])
            description = f"Mise en avant du projet '{project.title}'"
            
            # Notifier le propriétaire du projet
            create_system_notification(
                recipient=project.owner,
                title="Projet mis en avant",
                message=f"Votre projet '{project.title}' a été mis en avant sur la plateforme.",
                related_object=project 
            )
        
        elif action == 'unfeature':
            project.is_featured = False
            project.save(update_fields=['is_featured'])
            description = f"Retrait de la mise en avant du projet '{project.title}'"
        
        elif action == 'hide':
            project.is_hidden = True
            project.save(update_fields=['is_hidden'])
            description = f"Masquage du projet '{project.title}'"
            
            # Notifier le propriétaire du projet
            create_system_notification(
                recipient=project.owner,
                title="Projet masqué",
                message=f"Votre projet '{project.title}' a été masqué. Raison: {reason or 'Non spécifiée'}",
                related_object=project 
            )
        
        elif action == 'unhide':
            project.is_hidden = False
            project.save(update_fields=['is_hidden'])
            description = f"Affichage du projet '{project.title}'"
            
            # Notifier le propriétaire du projet
            create_system_notification(
                recipient=project.owner,
                title="Projet visible",
                message=f"Votre projet '{project.title}' est à nouveau visible sur la plateforme.",
                related_object=project 
            )
        
        # Ajouter la raison si elle est fournie
        if reason:
            description += f" - Raison: {reason}"
        
        # Enregistrer l'action dans le journal
        log_admin_action(
            admin_user=admin_user,
            action_type='project_validation',
            description=description,
            related_object=project,
            ip_address=self.context['request'].META.get('REMOTE_ADDR')
        )
        
        return project

class CommentModerationSerializer(serializers.Serializer):
    """
    Sérialiseur pour la modération des commentaires
    """
    comment_id = serializers.IntegerField(required=True)
    action = serializers.ChoiceField(
        choices=['approve', 'reject', 'hide'],
        required=True
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_comment_id(self, value):
        """
        Vérifie que le commentaire existe
        """
        from comments.models import Comment
        
        try:
            Comment.objects.get(id=value)
            return value
        except Comment.DoesNotExist:
            raise serializers.ValidationError("Le commentaire spécifié n'existe pas.")
    
    @transaction.atomic
    def save(self):
        """
        Exécute l'action sur le commentaire
        """
        from comments.models import Comment
        from notifications.utils import create_system_notification

        from .utils import log_admin_action
        
        comment_id = self.validated_data.get('comment_id')
        action = self.validated_data.get('action')
        reason = self.validated_data.get('reason', '')
        
        comment = Comment.objects.get(id=comment_id)
        admin_user = self.context['request'].user
        
        if action == 'approve':
            comment.is_moderated = True
            comment.is_approved = True
            comment.is_hidden = False
            comment.save(update_fields=['is_moderated', 'is_approved', 'is_hidden'])
            description = f"Approbation du commentaire #{comment.id}"
        
        elif action == 'reject':
            comment.is_moderated = True
            comment.is_approved = False
            comment.is_hidden = True
            comment.save(update_fields=['is_moderated', 'is_approved', 'is_hidden'])
            description = f"Rejet du commentaire #{comment.id}"
            
            # Notifier l'auteur du commentaire
            create_system_notification(
                recipient=comment.user,
                title="Commentaire rejeté",
                message=f"Votre commentaire sur le projet '{comment.project.title}' a été rejeté. Raison: {reason or 'Non spécifiée'}"
            )
        
        elif action == 'hide':
            comment.is_hidden = True
            comment.save(update_fields=['is_hidden'])
            description = f"Masquage du commentaire #{comment.id}"
            
            # Notifier l'auteur du commentaire
            create_system_notification(
                recipient=comment.user,
                title="Commentaire masqué",
                message=f"Votre commentaire sur le projet '{comment.project.title}' a été masqué. Raison: {reason or 'Non spécifiée'}"
            )
        
        # Ajouter la raison si elle est fournie
        if reason:
            description += f" - Raison: {reason}"
        
        # Enregistrer l'action dans le journal
        log_admin_action(
            admin_user=admin_user,
            action_type='comment_moderation',
            description=description,
            related_object=comment,
            ip_address=self.context['request'].META.get('REMOTE_ADDR')
        )
        
        return comment