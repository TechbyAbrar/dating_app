from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


# ------------------------ Hobbies Admin ------------------------ #
# @admin.register(Hobbies)
# class HobbiesAdmin(admin.ModelAdmin):
#     list_display = ("id", "hobby")
#     search_fields = ("hobby",)
#     ordering = ("id",)


# ------------------------ User Admin ------------------------ #
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "user_id",
        "email",
        "username",
        "full_name",
        "gender",
        "is_verified",
        "is_active",
        "is_staff",
        "is_subscribed",
        "created_at",
    )
    search_fields = ("email", "username", "full_name", "phone")
    list_filter = ("is_verified", "is_active", "is_staff", "gender", "country")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "otp", "otp_expired")

    fieldsets = (
        (None, {"fields": ("email", "username", "phone", "password")}),
        ("Personal Info", {
            "fields": (
                "full_name",
                "bio",
                "gender",
                "goal",
                "hoping_to_find",
                "looking_for",
                "dob",
                "age",
                "education",
                "height_feet",
                "height_inches",
                "country",
                "state",
                "location",
                "distance",
                "profile_pic",
                "profile_pic_url",
                "hobbies",
            )
        }),
        ("Subscription", {"fields": ("is_subscribed", "subscription_expiry")}),
        ("Permissions", {"fields": ("is_active", "is_verified", "is_staff", "is_superuser")}),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
        ("OTP", {"fields": ("otp", "otp_expired")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "password1", "password2"),
        }),
    )
