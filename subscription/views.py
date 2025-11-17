# views.py
import logging
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from .models import SubscriptionPlan, UserSubscription
from .serializers import (
    PublicSubscriptionPlanSerializer,
    AdminSubscriptionPlanSerializer,
    UserSubscriptionSerializer,
)
from .services import StripeService
from core.utils import ResponseHandler 

logger = logging.getLogger(__name__)


class SubscriptionPlanListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return all active subscription plans (no pagination).
        """
        try:
            queryset = SubscriptionPlan.objects.filter(active=True).select_related()
            serializer = PublicSubscriptionPlanSerializer(queryset, many=True)
            return ResponseHandler.success(
                message="Active subscription plans fetched successfully.",
                data=serializer.data,
            )
        except Exception as e:
            logger.exception("Failed to fetch subscription plans")
            return ResponseHandler.generic_error(exception=e)


class SubscriptionPlanDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Return a single active subscription plan.
        """
        try:
            plan = get_object_or_404(SubscriptionPlan, pk=pk, active=True)
            serializer = PublicSubscriptionPlanSerializer(plan)
            return ResponseHandler.success(
                message="Subscription plan details fetched successfully.",
                data=serializer.data,
            )
        except Exception as e:
            logger.exception(f"Error fetching subscription plan {pk}")
            return ResponseHandler.generic_error(exception=e)


class SubscriptionPlanCreateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = AdminSubscriptionPlanSerializer(data=request.data)
        if not serializer.is_valid():
            return ResponseHandler.bad_request(
                message="Validation failed.",
                errors=serializer.errors,
            )

        plan = serializer.save()
        try:
            product_id, price_id = StripeService.create_product_and_price(plan)
            plan.stripe_product_id = product_id
            plan.stripe_price_id = price_id
            plan.save(update_fields=["stripe_product_id", "stripe_price_id"])
            return ResponseHandler.created(
                message="Subscription plan created successfully.",
                data=AdminSubscriptionPlanSerializer(plan).data,
            )
        except Exception as e:
            # Remove plan to avoid inconsistent state
            try:
                plan.delete()
            except Exception:
                logger.exception("Failed deleting plan after Stripe sync failure")
            logger.exception(f"Stripe synchronization failed while creating plan: {e}")
            return ResponseHandler.server_error(
                message="Stripe synchronization failed",
                errors=str(e),
            )


class SubscriptionPlanUpdateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        """
        Admin updates a subscription plan. If price/currency changed, attempt Stripe update.
        """
        plan = get_object_or_404(SubscriptionPlan, pk=pk)
        serializer = AdminSubscriptionPlanSerializer(plan, data=request.data)
        if not serializer.is_valid():
            return ResponseHandler.bad_request(
                message="Validation failed.",
                errors=serializer.errors,
            )

        old_data = {
            "name": plan.name,
            "description": plan.description,
            "active": plan.active,
            "amount": plan.amount,
            "currency": plan.currency,
        }

        plan = serializer.save()

        changes = {
            "name": plan.name != old_data["name"],
            "description": plan.description != old_data["description"],
            "active": plan.active != old_data["active"],
            "price": plan.amount != old_data["amount"] or plan.currency != old_data["currency"],
        }

        try:
            if any(changes.values()):
                # Service returns (new_price_id, meta) or similar
                new_price_id, _ = StripeService.update_product_and_price(plan, changes)
                if new_price_id:
                    plan.stripe_price_id = new_price_id
                    plan.save(update_fields=["stripe_price_id"])
            return ResponseHandler.updated(
                message="Subscription plan updated successfully.",
                data=AdminSubscriptionPlanSerializer(plan).data,
            )
        except Exception as e:
            logger.exception(f"Stripe update failed for plan {pk}: {e}")
            return ResponseHandler.server_error(
                message="Stripe synchronization failed",
                errors=str(e),
            )


class PurchaseSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, plan_id):
        """
        Create a checkout session for a user to purchase a subscription plan.
        """
        try:
            plan = get_object_or_404(SubscriptionPlan, id=plan_id, active=True)
            user = request.user
            subscription, _ = UserSubscription.objects.get_or_create(user=user)

            if subscription.is_active:
                return ResponseHandler.conflict(
                    message="Active subscription exists."
                )

            if not subscription.stripe_customer_id:
                try:
                    customer_id = StripeService.create_customer(
                        user.email, user.get_full_name() or user.username
                    )
                    subscription.stripe_customer_id = customer_id
                    subscription.save(update_fields=["stripe_customer_id"])
                except Exception as e:
                    logger.exception(f"Stripe customer creation failed for user {user.user_id}: {e}")
                    return ResponseHandler.server_error(
                        message="Customer creation failed",
                        errors=str(e),
                    )

            try:
                session = StripeService.create_checkout_session(
                    subscription.stripe_customer_id, plan.stripe_price_id, user.user_id, plan.id
                )
                subscription.stripe_checkout_session_id = session.id
                subscription.save(update_fields=["stripe_checkout_session_id"])
            except Exception as e:
                logger.exception(f"Checkout session creation failed for user {user.user_id}: {e}")
                return ResponseHandler.server_error(
                    message="Checkout session failed",
                    errors=str(e),
                )

            return ResponseHandler.created(
                message="Checkout session created successfully.",
                data={"checkout_url": session.url},
            )
        except Exception as e:
            logger.exception("Unhandled error in PurchaseSubscriptionAPIView")
            return ResponseHandler.generic_error(exception=e)


class MySubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return the requesting user's subscription object.
        """
        try:
            subscription, _ = UserSubscription.objects.get_or_create(user=request.user)
            serializer = UserSubscriptionSerializer(subscription)
            return ResponseHandler.success(
                message="User subscription retrieved successfully.",
                data=serializer.data,
            )
        except Exception as e:
            logger.exception(f"Error fetching subscription for user {request.user.id}")
            return ResponseHandler.generic_error(exception=e)


class CancelSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Cancel the authenticated user's active subscription.
        """
        try:
            subscription = getattr(request.user, "subscription", None)
            if not subscription or not subscription.is_active:
                return ResponseHandler.bad_request(
                    message="No active subscription"
                )

            subscription.cancel()
            logger.info(f"Subscription canceled for user {request.user.user_id}")

            # Optional: prorated refund (uncomment for production)
            # if subscription.stripe_payment_intent_id:
            #     try:
            #         pi = stripe.PaymentIntent.retrieve(subscription.stripe_payment_intent_id)
            #         amount_refundable = pi.amount - pi.amount_received  # example logic
            #         if amount_refundable > 0:
            #             stripe.Refund.create(payment_intent=pi.id, amount=amount_refundable)
            #     except Exception as e:
            #         logger.error(f"Refund failed: {e}")

            return ResponseHandler.success(
                message="Subscription canceled successfully."
            )
        except Exception as e:
            logger.exception(f"Subscription cancel failed for user {request.user.user_id}")
            return ResponseHandler.generic_error(exception=e)



# webhook handler
import logging
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from dateutil.relativedelta import relativedelta
from django.shortcuts import get_object_or_404
from subscription.models import SubscriptionPlan, UserSubscription

from django.contrib.auth import get_user_model
User = get_user_model()

logger = logging.getLogger(__name__)


@csrf_exempt
def stripe_webhook(request):
    """Stripe webhook handler — validates signature, handles checkout completion, and activates subscriptions."""
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    # --- Validate signature ---
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.error(f"[STRIPE] Invalid payload or signature: {e}")
        return HttpResponse(status=400)
    except Exception as e:
        logger.exception("[STRIPE] Unexpected error constructing event")
        return HttpResponse(status=400)

    # --- Process events ---
    try:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            mode = getattr(session, "mode", None)
            payment_status = getattr(session, "payment_status", None)

            # Only process paid sessions
            if payment_status != "paid":
                logger.info(f"[STRIPE] Ignoring session: payment_status={payment_status}")
                return HttpResponse(status=200)

            user_id = getattr(session, "client_reference_id", None)
            metadata = getattr(session, "metadata", {}) or {}
            plan_id = metadata.get("plan_id")

            if not user_id or not plan_id:
                logger.warning("[STRIPE] Missing required metadata: user_id or plan_id.")
                return HttpResponse(status=200)

            # --- Retrieve user and plan ---
            try:
                # ✅ Corrected field lookup: use user_id, not id
                user = get_object_or_404(User, user_id=user_id)
                plan = get_object_or_404(SubscriptionPlan, id=plan_id)
                subscription, _ = UserSubscription.objects.get_or_create(user=user)
            except Exception as e:
                logger.exception(f"[STRIPE] Lookup failure for user_id={user_id}, plan_id={plan_id}: {e}")
                return HttpResponse(status=200)

            # --- Idempotency check ---
            session_id = getattr(session, "id", None)
            if subscription.stripe_checkout_session_id == session_id:
                logger.info(f"[STRIPE] Duplicate event ignored for user_id={user_id}")
                return HttpResponse(status=200)

            # --- Activate subscription ---
            try:
                start_date = timezone.now()
                end_date = start_date + relativedelta(months=+plan.duration_months)

                subscription.plan = plan
                subscription.status = "active"
                subscription.is_active = True
                subscription.subscription_start = start_date
                subscription.subscription_end = end_date
                subscription.stripe_payment_intent_id = getattr(session, "payment_intent", None)
                subscription.stripe_checkout_session_id = session_id
                subscription.stripe_customer_id = getattr(session, "customer", None)
                subscription.save(update_fields=[
                    "plan", "status", "is_active",
                    "subscription_start", "subscription_end",
                    "stripe_payment_intent_id", "stripe_checkout_session_id",
                    "stripe_customer_id", "updated_at"
                ])

                logger.info(f"[STRIPE] ✅ Activated subscription for user_id={user_id}, plan={plan.name}")
            except Exception as e:
                logger.exception(f"[STRIPE] Failed to activate subscription for user_id={user_id}: {e}")
                return HttpResponse(status=200)

    except Exception as e:
        logger.exception(f"[STRIPE] Unexpected error processing webhook: {e}")
        return HttpResponse(status=200)

    return HttpResponse(status=200)
