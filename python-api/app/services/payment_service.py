import stripe
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, Subscription, SubscriptionPlan

# Initialize Stripe
stripe.api_key = settings.STRIPE_API_KEY

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        if not settings.STRIPE_API_KEY:
            logger.warning("Stripe API key not set. Payment service functionality will be limited.")
    
    def create_customer(self, db: Session, user: User) -> str:
        """Create a new Stripe customer for the user"""
        if not settings.STRIPE_API_KEY:
            logger.error("Stripe API key not set")
            return None
        
        try:
            # Create a new customer in Stripe
            customer = stripe.Customer.create(
                email=user.email,
                name=user.username,
                metadata={
                    "user_id": str(user.id)
                }
            )
            
            # Return the customer ID
            return customer.id
            
        except Exception as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            return None
    
    def create_subscription(
        self, 
        db: Session, 
        user: User, 
        plan: SubscriptionPlan
    ) -> Optional[Subscription]:
        """Create a new subscription for a user"""
        if not settings.STRIPE_API_KEY:
            logger.error("Stripe API key not set")
            return None
        
        # Check if user has a Stripe customer ID
        if not user.subscriptions or not user.subscriptions[0].stripe_customer_id:
            customer_id = self.create_customer(db, user)
            if not customer_id:
                logger.error(f"Failed to create Stripe customer for user {user.id}")
                return None
        else:
            customer_id = user.subscriptions[0].stripe_customer_id
        
        try:
            # Create a subscription in Stripe
            stripe_subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[
                    {"price": plan.stripe_price_id},
                ],
                metadata={
                    "user_id": str(user.id),
                    "plan_id": str(plan.id)
                }
            )
            
            # Create subscription record in database
            subscription = Subscription(
                user_id=user.id,
                plan_id=plan.id,
                status=stripe_subscription.status,
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=customer_id,
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                cancel_at_period_end=stripe_subscription.cancel_at_period_end
            )
            
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            db.rollback()
            return None
    
    def cancel_subscription(self, db: Session, subscription: Subscription) -> bool:
        """Cancel a user's subscription"""
        if not settings.STRIPE_API_KEY:
            logger.error("Stripe API key not set")
            return False
        
        if not subscription.stripe_subscription_id:
            logger.error(f"Subscription {subscription.id} does not have a Stripe subscription ID")
            return False
        
        try:
            # Cancel subscription in Stripe
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            # Update subscription in database
            subscription.cancel_at_period_end = True
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            db.rollback()
            return False
    
    def update_subscription_status(self, db: Session, subscription: Subscription) -> bool:
        """Update subscription status from Stripe"""
        if not settings.STRIPE_API_KEY:
            logger.error("Stripe API key not set")
            return False
        
        if not subscription.stripe_subscription_id:
            logger.error(f"Subscription {subscription.id} does not have a Stripe subscription ID")
            return False
        
        try:
            # Get subscription from Stripe
            stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            
            # Update subscription in database
            subscription.status = stripe_subscription.status
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
            subscription.cancel_at_period_end = stripe_subscription.cancel_at_period_end
            
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update subscription status: {e}")
            db.rollback()
            return False
    
    def handle_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """Handle Stripe webhook events"""
        if not settings.STRIPE_API_KEY or not settings.STRIPE_WEBHOOK_SECRET:
            logger.error("Stripe API key or webhook secret not set")
            return False
        
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Process event based on type
            if event.type == "customer.subscription.created":
                logger.info(f"Subscription created: {event.data.object.id}")
                # Handle subscription created
                
            elif event.type == "customer.subscription.updated":
                logger.info(f"Subscription updated: {event.data.object.id}")
                # Handle subscription updated
                
            elif event.type == "customer.subscription.deleted":
                logger.info(f"Subscription deleted: {event.data.object.id}")
                # Handle subscription deleted
                
            elif event.type == "invoice.payment_succeeded":
                logger.info(f"Invoice payment succeeded: {event.data.object.id}")
                # Handle successful payment
                
            elif event.type == "invoice.payment_failed":
                logger.info(f"Invoice payment failed: {event.data.object.id}")
                # Handle failed payment
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle webhook: {e}")
            return False
    
    def create_billing_portal_session(self, customer_id: str) -> Optional[str]:
        """Create a billing portal session for a customer"""
        if not settings.STRIPE_API_KEY:
            logger.error("Stripe API key not set")
            return None
        
        try:
            # Create billing portal session
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=f"https://yourdomain.com/account"
            )
            
            return session.url
            
        except Exception as e:
            logger.error(f"Failed to create billing portal session: {e}")
            return None
    
    def create_checkout_session(
        self, 
        plan: SubscriptionPlan,
        customer_id: Optional[str] = None
    ) -> Optional[str]:
        """Create a checkout session for a subscription"""
        if not settings.STRIPE_API_KEY:
            logger.error("Stripe API key not set")
            return None
        
        try:
            # Create checkout session parameters
            params = {
                "mode": "subscription",
                "line_items": [
                    {
                        "price": plan.stripe_price_id,
                        "quantity": 1,
                    },
                ],
                "success_url": "https://yourdomain.com/subscription/success?session_id={CHECKOUT_SESSION_ID}",
                "cancel_url": "https://yourdomain.com/subscription/cancel",
            }
            
            # Add customer ID if provided
            if customer_id:
                params["customer"] = customer_id
            
            # Create checkout session
            session = stripe.checkout.Session.create(**params)
            
            return session.url
            
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            return None
    
    def get_usage_balance(self, subscription: Subscription) -> Dict[str, Any]:
        """Get usage balance for a subscription"""
        # This is a placeholder implementation
        # In a real application, you would track token usage in your database
        total_tokens = subscription.plan.token_limit
        used_tokens = 0  # Get from usage records
        
        return {
            "total_tokens": total_tokens,
            "used_tokens": used_tokens,
            "remaining_tokens": total_tokens - used_tokens,
            "usage_percentage": (used_tokens / total_tokens) * 100 if total_tokens > 0 else 0
        }

# Create a singleton instance
payment_service = PaymentService()
