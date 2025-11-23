from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import UserLike
from notification.models import Notification

@receiver(post_save, sender=UserLike)
def create_like_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            sender=instance.user_from,
            receiver=instance.user_to,
            content_type=ContentType.objects.get_for_model(UserLike),
            object_id=instance.id,
            message=f"{instance.user_from.get_full_name()} liked your profile"
        )
