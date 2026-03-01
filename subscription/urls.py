# urls.py
from django.urls import path
from .views import (
    CurrentSubscriptionView,
    AvailablePlansView,
    SubscriptionDetailView,
    RevenueCatWebhookView
)

urlpatterns = [
    # Subscription endpoints
    path('subscription/current/', CurrentSubscriptionView.as_view(), name='current-subscription'),
    path('subscription/detail/', SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('subscription/plans/', AvailablePlansView.as_view(), name='available-plans'),
    
    # Webhook
    path('webhooks/revenuecat/', RevenueCatWebhookView.as_view(), name='revenuecat-webhook'),
]