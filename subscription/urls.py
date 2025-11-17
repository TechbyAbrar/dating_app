# urls.py (example routing)
from django.urls import path
from .views import (
    SubscriptionPlanListAPIView, SubscriptionPlanDetailAPIView,
    SubscriptionPlanCreateAPIView, SubscriptionPlanUpdateAPIView,
    PurchaseSubscriptionAPIView, MySubscriptionAPIView, CancelSubscriptionAPIView, stripe_webhook
)

urlpatterns = [
    path("plans/", SubscriptionPlanListAPIView.as_view(), name="plan-list"),
    path("plans/<int:pk>/", SubscriptionPlanDetailAPIView.as_view(), name="plan-detail"),
    path("admin/plans/create/", SubscriptionPlanCreateAPIView.as_view(), name="plan-create"),
    path("admin/plans/<int:pk>/update/", SubscriptionPlanUpdateAPIView.as_view(), name="plan-update"),
    path("plans/<int:plan_id>/purchase/", PurchaseSubscriptionAPIView.as_view(), name="plan-purchase"),
    path("my-subscription/", MySubscriptionAPIView.as_view(), name="my-subscription"),
    path("my-subscription/cancel/", CancelSubscriptionAPIView.as_view(), name="subscription-cancel"),
    path("webhook/stripe/", stripe_webhook, name="stripe-webhook"),
]


