# # chat/models.py
# from django.db import models
# from django.conf import settings

# class Message(models.Model):
#     sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sent_messages", on_delete=models.CASCADE)
#     receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="received_messages", on_delete=models.CASCADE)
#     text = models.TextField(blank=True, null=True)
#     media = models.FileField(upload_to="chat_media/", blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     is_read = models.BooleanField(default=False)

#     class Meta:
#         ordering = ["created_at"]
#         indexes = [
#             models.Index(fields=["sender", "receiver", "created_at"]),
#         ]

#     def __str__(self):
#         return f"{self.sender} -> {self.receiver} at {self.created_at}"
