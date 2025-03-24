# messaging/serializers.py
from rest_framework import serializers
from .models import Conversation, Message
from users.serializers import UserProfileSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les messages
    """
    sender = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'created_at', 'is_read']
        read_only_fields = ['id', 'conversation', 'sender', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les conversations
    """
    participants = UserProfileSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'created_at', 'updated_at', 'last_message', 'unread_count', 'other_participant']
        read_only_fields = ['id', 'participants', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        """
        Récupère le dernier message de la conversation
        """
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'id': last_message.id,
                'content': last_message.content,
                'sender_id': last_message.sender.id,
                'sender_name': f"{last_message.sender.first_name} {last_message.sender.last_name}",
                'created_at': last_message.created_at,
                'is_read': last_message.is_read
            }
        return None
    
    def get_unread_count(self, obj):
        """
        Compte le nombre de messages non lus dans la conversation
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0
    
    def get_other_participant(self, obj):
        """
        Récupère l'autre participant de la conversation (dans le cas d'une conversation à deux)
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj.participants.count() == 2:
            other = obj.participants.exclude(id=request.user.id).first()
            if other:
                return {
                    'id': other.id,
                    'username': other.username,
                    'first_name': other.first_name,
                    'last_name': other.last_name,
                    'profile_picture': request.build_absolute_uri(other.profile_picture.url) if other.profile_picture else None
                }
        return None

class ConversationCreateSerializer(serializers.Serializer):
    """
    Sérialiseur pour la création d'une conversation
    """
    recipient_id = serializers.IntegerField(required=True)
    message = serializers.CharField(required=True)
    
    def validate_recipient_id(self, value):
        """
        Vérifie que le destinataire existe
        """
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Le destinataire spécifié n'existe pas.")
        
        # Vérifier que le destinataire n'est pas l'expéditeur
        if self.context['request'].user.id == value:
            raise serializers.ValidationError("Vous ne pouvez pas envoyer un message à vous-même.")
        
        return value
    
    def create(self, validated_data):
        """
        Crée une nouvelle conversation avec un premier message
        """
        sender = self.context['request'].user
        recipient_id = validated_data['recipient_id']
        recipient = User.objects.get(id=recipient_id)
        message_content = validated_data['message']
        
        # Vérifier si une conversation existe déjà entre ces deux utilisateurs
        conversations = Conversation.objects.filter(participants=sender).filter(participants=recipient)
        
        if conversations.exists():
            # Utiliser la conversation existante
            conversation = conversations.first()
        else:
            # Créer une nouvelle conversation
            conversation = Conversation.objects.create()
            conversation.participants.add(sender, recipient)
        
        # Créer le message
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=message_content
        )
        
        # Mettre à jour la date de la conversation
        conversation.save()  # updated_at sera mis à jour automatiquement
        
        return conversation