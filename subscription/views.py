# views.py
import hmac
import hashlib
import json
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserSubscription, SubscriptionPlan, SubscriptionEvent
from .serializers import UserSubscriptionSerializer, SubscriptionPlanSerializer

User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class RevenueCatWebhookView(APIView):
    """Handle RevenueCat webhook events"""
    
    def verify_webhook(self, request):
        """Verify webhook signature from RevenueCat"""
        signature = request.headers.get('X-Revenuecat-Signature')
        if not signature:
            return False
        
        # Get your webhook secret from settings
        from django.conf import settings
        secret = settings.REVENUECAT_WEBHOOK_SECRET
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode(),
            request.body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def post(self, request):
        # Verify webhook authenticity
        if not self.verify_webhook(request):
            return Response(
                {'error': 'Invalid signature'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        event_data = request.data
        event_type = event_data.get('type')
        
        try:
            if event_type == 'INITIAL_PURCHASE':
                self.handle_initial_purchase(event_data)
            elif event_type == 'RENEWAL':
                self.handle_renewal(event_data)
            elif event_type == 'CANCELLATION':
                self.handle_cancellation(event_data)
            elif event_type == 'EXPIRATION':
                self.handle_expiration(event_data)
            elif event_type == 'BILLING_ISSUE':
                self.handle_billing_issue(event_data)
            elif event_type == 'UNCANCELLATION':
                self.handle_reactivation(event_data)
            # Add more event types as needed
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
            
            return Response(
                {'error': 'Processing failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def handle_initial_purchase(self, event_data):
        from .models import UserSubscription, SubscriptionPlan, SubscriptionEvent
        
        subscriber_id = event_data['event']['app_user_id']
        product_id = event_data['event']['product_id']
        
        # Get or create user subscription
        try:
            user = User.objects.get(id=subscriber_id)  # Adjust based on your user ID mapping
        except User.DoesNotExist:
            return
        
        plan = SubscriptionPlan.objects.get(plan_id=product_id)
        
        subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            defaults={
                'revenuecat_subscriber_id': subscriber_id,
                'plan': plan,
                'status': 'active',
                'is_active': True,
                'store': event_data['event']['store'],
            }
        )
        
        # Update subscription details
        subscription.plan = plan
        subscription.status = 'active'
        subscription.is_active = True
        subscription.started_at = timezone.now()
        subscription.expires_at = timezone.datetime.fromisoformat(
            event_data['event']['expiration_at_ms']
        ) if event_data['event'].get('expiration_at_ms') else None
        subscription.original_transaction_id = event_data['event'].get('original_transaction_id', '')
        subscription.save()
        
        # Log event
        SubscriptionEvent.objects.create(
            user_subscription=subscription,
            event_type='initial_purchase',
            event_timestamp=timezone.now(),
            revenuecat_event_id=event_data.get('id'),
            raw_data=event_data,
            transaction_id=event_data['event'].get('transaction_id', ''),
            price=event_data['event'].get('price'),
            currency=event_data['event'].get('currency', 'USD')
        )
    
    def handle_cancellation(self, event_data):
        from .models import UserSubscription, SubscriptionEvent
        
        subscriber_id = event_data['event']['app_user_id']
        
        try:
            subscription = UserSubscription.objects.get(revenuecat_subscriber_id=subscriber_id)
            subscription.status = 'cancelled'
            subscription.will_renew = False
            subscription.cancelled_at = timezone.now()
            subscription.save()
            
            SubscriptionEvent.objects.create(
                user_subscription=subscription,
                event_type='cancellation',
                event_timestamp=timezone.now(),
                revenuecat_event_id=event_data.get('id'),
                raw_data=event_data
            )
        except UserSubscription.DoesNotExist:
            pass
    
    # Implement other handlers similarly...
    
# views.py
class CurrentSubscriptionView(APIView):
    """Get current user's subscription status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            serializer = UserSubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserSubscription.DoesNotExist:
            return Response({
                'status': 'expired',
                'is_active': False,
                'message': 'No active subscription'
            }, status=status.HTTP_200_OK)


class AvailablePlansView(APIView):
    """Get all available subscription plans"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscriptionDetailView(APIView):
    """Get detailed subscription information"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            subscription = UserSubscription.objects.select_related('plan').get(user=request.user)
            serializer = UserSubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserSubscription.DoesNotExist:
            return Response({
                'detail': 'Subscription not found'
            }, status=status.HTTP_404_NOT_FOUND)