# services/stripe_service.py (OOP, reusable, testable, microservice-style separation)
import stripe
import logging
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


class StripeService:
    @staticmethod
    def create_customer(email: str, name: str):
        try:
            customer = stripe.Customer.create(email=email, name=name)
            logger.info(f"Stripe customer created: {customer.id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            raise

    @staticmethod
    def create_product_and_price(plan):
        try:
            product = stripe.Product.create(
                name=plan.name,
                description=plan.description or None,
                active=plan.active,
                metadata={"plan_type": plan.plan_type},
            )
            price = stripe.Price.create(
                product=product.id,
                unit_amount=plan.price_in_cents,
                currency=plan.currency,
            )
            logger.info(f"Stripe product {product.id} & price {price.id} created for plan {plan.id}")
            return product.id, price.id
        except stripe.error.StripeError as e:
            logger.error(f"Stripe product/price creation failed: {e}")
            raise

    @staticmethod
    def update_product_and_price(plan, changes: dict):
        updated = False
        if plan.stripe_product_id:
            product_updates = {}
            if changes.get("name"):
                product_updates["name"] = plan.name
            if changes.get("description"):
                product_updates["description"] = plan.description or None
            if changes.get("active"):
                product_updates["active"] = plan.active
            if product_updates:
                stripe.Product.modify(plan.stripe_product_id, **product_updates)
                updated = True

        if changes.get("price"):
            if plan.stripe_price_id:
                stripe.Price.modify(plan.stripe_price_id, active=False)
            price = stripe.Price.create(
                product=plan.stripe_product_id,
                unit_amount=plan.price_in_cents,
                currency=plan.currency,
            )
            logger.info(f"New Stripe price {price.id} for plan {plan.id}")
            return price.id, updated
        return None, updated

    @staticmethod
    def create_checkout_session(customer_id: str, price_id: str, user_id: int, plan_id: int):
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="payment",
                success_url=f"{settings.FRONTEND_SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=settings.FRONTEND_CANCEL_URL,
                client_reference_id=str(user_id),
                metadata={"plan_id": str(plan_id)},
            )
            logger.info(f"Checkout session {session.id} created for user {user_id}")
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Checkout session creation failed: {e}")
            raise