from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

User = get_user_model()

class Notification(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications_sent"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications_received"
    )

    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    message = models.TextField()

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["receiver", "is_read"]),
            models.Index(fields=["receiver", "created_at"]),
        ]

    def __str__(self):
        return f"To {self.receiver} from {self.sender}"
