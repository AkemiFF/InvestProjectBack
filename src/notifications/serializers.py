# notifications/serializers.py
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les notifications
    """
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'notification_type', 'title', 'message',
            'related_object_id', 'related_object_type', 'created_at', 'is_read'
        ]
        read_only_fields = [
            'id', 'recipient', 'notification_type', 'title', 'message',
            'related_object_id', 'related_object_type', 'created_at'
        ]