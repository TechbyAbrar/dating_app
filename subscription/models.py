from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SubscriptionPlan(models.Model):
    """Store available subscription plans"""
    PLAN_TYPES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('premium_plus', 'Premium Plus'),
    ]
    
    plan_id = models.CharField(max_length=100, unique=True)  # RevenueCat product ID
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    duration_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    features = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.plan_type}"


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('trial', 'Trial'),
        ('grace_period', 'Grace Period'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    
    # RevenueCat specific fields
    revenuecat_subscriber_id = models.CharField(max_length=255, unique=True)
    original_transaction_id = models.CharField(max_length=255, blank=True)
    
    # Subscription status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='expired')
    is_active = models.BooleanField(default=False)
    will_renew = models.BooleanField(default=True)
    
    # Dates
    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Trial info
    is_trial = models.BooleanField(default=False)
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Additional metadata
    store = models.CharField(max_length=20)  # 'app_store' or 'play_store'
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.status}"
    
    @property
    def is_valid(self):
        """Check if subscription is currently valid"""
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class SubscriptionEvent(models.Model):
    """Log all subscription events for audit trail"""
    EVENT_TYPES = [
        ('initial_purchase', 'Initial Purchase'),
        ('renewal', 'Renewal'),
        ('cancellation', 'Cancellation'),
        ('reactivation', 'Reactivation'),
        ('expiration', 'Expiration'),
        ('refund', 'Refund'),
        ('trial_started', 'Trial Started'),
        ('trial_converted', 'Trial Converted'),
        ('billing_issue', 'Billing Issue'),
    ]
    
    user_subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    event_timestamp = models.DateTimeField()
    
    # RevenueCat webhook data
    revenuecat_event_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    raw_data = models.JSONField(default=dict)
    
    # Transaction details
    transaction_id = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-event_timestamp']
        indexes = [
            models.Index(fields=['user_subscription', '-event_timestamp']),
        ]