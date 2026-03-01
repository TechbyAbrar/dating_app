# serializers.py
from rest_framework import serializers
from .models import UserSubscription, SubscriptionPlan
class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['plan_id', 'name', 'plan_type', 'duration_days', 
                  'price', 'currency', 'features']

class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = ['status', 'is_active', 'plan_details', 'started_at', 
                  'expires_at', 'is_trial', 'will_renew', 'is_valid']


