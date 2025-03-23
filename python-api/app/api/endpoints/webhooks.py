from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
import json
import stripe
from datetime import datetime

from app.db.base import get_db
from app.core.config import settings
from app.models.user import User, Subscription

router = APIRouter()

@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(get_db)
) -> Any:
    """
    Handle Stripe webhook events for subscription updates
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature header"
        )
    
    # Get the request body
    payload = await request.body()
    
    try:
        # Verify the event
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe signature"
        )
    
    # Handle the event
    if event["type"] == "checkout.session.completed":
        # Get the checkout session
        session = event["data"]["object"]
        
        # Get customer and subscription info
        customer_id = session["customer"]
        subscription_id = session["subscription"]
        
        # Get the subscription from Stripe
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        stripe_price_id = stripe_subscription["items"]["data"][0]["price"]["id"]
        
        # Find the user by customer ID
        subscription = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()
        
        # If the subscription doesn't exist, find the user by client reference ID
        if not subscription and "client_reference_id" in session:
            user_id = session["client_reference_id"]
            user = db.query(User).filter(User.id == user_id).first()
            
            if user:
                # Create a new subscription
                subscription = Subscription(
                    user_id=user.id,
                    stripe_subscription_id=subscription_id,
                    stripe_customer_id=customer_id,
                    stripe_price_id=stripe_price_id,
                    status="active",
                    start_date=datetime.fromtimestamp(stripe_subscription["current_period_start"]),
                    end_date=datetime.fromtimestamp(stripe_subscription["current_period_end"])
                )
                db.add(subscription)
                db.commit()
        
    elif event["type"] == "customer.subscription.updated":
        # Get the subscription
        stripe_subscription = event["data"]["object"]
        subscription_id = stripe_subscription["id"]
        
        # Update the subscription in the database
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if subscription:
            # Update subscription details
            subscription.status = stripe_subscription["status"]
            subscription.end_date = datetime.fromtimestamp(stripe_subscription["current_period_end"])
            
            # If price has changed, update it
            new_price_id = stripe_subscription["items"]["data"][0]["price"]["id"]
            if subscription.stripe_price_id != new_price_id:
                subscription.stripe_price_id = new_price_id
            
            db.commit()
    
    elif event["type"] == "customer.subscription.deleted":
        # Get the subscription
        stripe_subscription = event["data"]["object"]
        subscription_id = stripe_subscription["id"]
        
        # Update the subscription in the database
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if subscription:
            subscription.status = "canceled"
            subscription.canceled_at = datetime.utcnow()
            db.commit()
    
    return {"status": "success"}
