# comments/serializers.py
from rest_framework import serializers
from .models import Comment
from users.serializers import UserProfileSerializer

class RecursiveCommentSerializer(serializers.Serializer):
    """
    Sérialiseur récursif pour les réponses aux commentaires
    """
    def to_representation(self, instance):
        serializer = CommentSerializer(instance, context=self.context)
        return serializer.data

class CommentSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les commentaires
    """
    author = UserProfileSerializer(read_only=True)
    replies = RecursiveCommentSerializer(many=True, read_only=True)
    is_owner = serializers.SerializerMethodField()
    can_moderate = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'project', 'author', 'parent', 'content', 
            'created_at', 'updated_at', 'is_approved', 'replies',
            'is_owner', 'can_moderate'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'is_approved', 'replies']
    
    def get_is_owner(self, obj):
        """
        Vérifie si l'utilisateur actuel est l'auteur du commentaire
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user
        return False
    
    def get_can_moderate(self, obj):
        """
        Vérifie si l'utilisateur actuel peut modérer le commentaire
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # L'auteur du projet peut modérer les commentaires
            return (obj.project.owner == request.user) or request.user.is_staff
        return False

class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création de commentaires
    """
    class Meta:
        model = Comment
        fields = ['project', 'parent', 'content']
    
    def validate_parent(self, value):
        """
        Vérifie que le parent est un commentaire du même projet
        """
        if value and value.project.id != self.initial_data.get('project'):
            raise serializers.ValidationError("Le commentaire parent doit appartenir au même projet.")
        return value
    
    def create(self, validated_data):
        """
        Crée un nouveau commentaire avec l'auteur actuel
        """
        validated_data['author'] = self.context['request'].user
        
        # Si c'est un commentaire de premier niveau, il est approuvé par défaut
        # Si c'est une réponse, il hérite du statut d'approbation du parent
        if not validated_data.get('parent'):
            validated_data['is_approved'] = True
        else:
            validated_data['is_approved'] = validated_data['parent'].is_approved
        
        return super().create(validated_data)

class CommentUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour de commentaires
    """
    class Meta:
        model = Comment
        fields = ['content']

class CommentModerationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la modération de commentaires
    """
    class Meta:
        model = Comment
        fields = ['is_approved']