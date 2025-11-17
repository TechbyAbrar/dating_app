from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom manager for User model supporting email, phone, and username.
    """

    def _create_user(self, email=None, phone=None, username=None, password=None, **extra_fields):
        if not email and not phone and not username:
            raise ValueError(_("User must have at least one identifier: email, phone, or username"))

        if email:
            email = self.normalize_email(email)

        user = self.model(email=email, phone=phone, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, phone=None, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_verified", False)
        return self._create_user(email, phone, username, password, **extra_fields)

    def create_superuser(self, email=None, phone=None, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        if not extra_fields.get("is_staff") or not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_staff=True and is_superuser=True"))

        return self._create_user(email, phone, username, password, **extra_fields)