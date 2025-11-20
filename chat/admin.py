from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ChatThread, Message, MessageReaction

@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "user_a", "user_b", "created_at", "updated_at")
    search_fields = ("user_a__username", "user_b__username")
    list_filter = ("created_at", "updated_at")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "thread", "sender", "message_type", "is_read", "is_like", "created_at")
    search_fields = ("sender__username", "content")
    list_filter = ("message_type", "is_read", "is_like", "created_at")

@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "user", "reaction", "created_at")
    search_fields = ("user__username", "reaction")
    list_filter = ("reaction", "created_at")
