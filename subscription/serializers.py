# serializers.py (clean separation - public vs admin)
from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription


class PublicSubscriptionPlanSerializer(serializers.ModelSerializer):
    price_in_cents = serializers.ReadOnlyField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id", "plan_type", "name", "description", "amount", "duration_months",
            "details", "currency", "active", "created_at", "updated_at", "price_in_cents"
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value

    def validate_duration_months(self, value):
        if value <= 0:
            raise serializers.ValidationError("Duration must be positive.")
        return value


class AdminSubscriptionPlanSerializer(PublicSubscriptionPlanSerializer):
    stripe_product_id = serializers.CharField(read_only=True)
    stripe_price_id = serializers.CharField(read_only=True)

    class Meta(PublicSubscriptionPlanSerializer.Meta):
        fields = PublicSubscriptionPlanSerializer.Meta.fields + ["stripe_product_id", "stripe_price_id"]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = PublicSubscriptionPlanSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            "plan", "status", "subscription_start", "subscription_end",
            "is_active", "created_at", "updated_at"
        ]