# models.py (updated - clean, minimal changes, removed unused subscription_id, added necessary fields for one-time payments)
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from dateutil.relativedelta import relativedelta  # pip install python-dateutil

User = get_user_model()


class SubscriptionPlan(models.Model):
    PLAN_TYPE_CHOICES = (
        ("basic", "Basic"),
        ("premium", "Premium"),
        ("vip", "VIP"),
    )

    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total price for the entire duration")
    duration_months = models.PositiveIntegerField(help_text="Validity in months (e.g., 3, 6, 12)")
    details = models.JSONField(default=dict, blank=True)

    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    currency = models.CharField(max_length=10, default="usd")
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["amount"]  # Logical ordering for list API
        indexes = [models.Index(fields=["plan_type"]), models.Index(fields=["active"])]

    def __str__(self):
        return f"{self.plan_type.capitalize()} - {self.duration_months} months"

    @property
    def price_in_cents(self) -> int:
        return int(self.amount * 100)


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("canceled", "Canceled"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="inactive")

    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)

    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["stripe_checkout_session_id"])]

    def __str__(self):
        return f"{self.user.email} - {self.status}"

    @property
    def is_active(self) -> bool:
        if self.status != "active":
            return False
        if self.subscription_end and timezone.now() > self.subscription_end:
            self.status = "inactive"
            self.save(update_fields=["status", "updated_at"])
            return False
        return True

    def activate(self, start=None, end=None):
        self.status = "active"
        self.subscription_start = start or timezone.now()
        self.subscription_end = end
        self.save(update_fields=["status", "subscription_start", "subscription_end", "updated_at"])

    def cancel(self):
        self.status = "canceled"
        self.subscription_end = timezone.now()
        self.save(update_fields=["status", "subscription_end", "updated_at"])