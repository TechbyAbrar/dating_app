from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_profile = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "sender",
            "sender_name",
            "sender_profile",
            "message",
            "is_read",
            "created_at",
        ]

    def get_sender_name(self, obj):
        return obj.sender.full_name or obj.sender.username

    def get_sender_profile(self, obj):
        return obj.sender.profile_pic_url or (
            obj.sender.profile_pic.url if obj.sender.profile_pic else None
        )
