from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User, Subscription, SubscriptionPlan
from app.api.schemas.subscription import (
    SubscriptionPlanRead, 
    SubscriptionRead,
    UsageBalance
)
from app.services.payment_service import payment_service
from app.api.dependencies import get_current_user, get_current_active_user

router = APIRouter()

@router.get("/plans", response_model=List[SubscriptionPlanRead])
def list_subscription_plans(
    db: Session = Depends(get_db)
) -> Any:
    """
    List all available subscription plans
    """
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()
    return plans

@router.get("/my-subscription", response_model=SubscriptionRead)
def get_current_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get the current user's active subscription
    """
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    return subscription

@router.post("/subscribe/{plan_id}", response_model=dict)
def create_subscription(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new subscription for the current user
    """
    # Check if user already has an active subscription
    existing_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription"
        )
    
    # Get the subscription plan
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id,
        SubscriptionPlan.is_active == True
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    
    # Create a checkout session URL
    customer_id = None
    if current_user.subscriptions:
        for sub in current_user.subscriptions:
            if sub.stripe_customer_id:
                customer_id = sub.stripe_customer_id
                break
    
    checkout_url = payment_service.create_checkout_session(plan, customer_id)
    
    if not checkout_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription checkout session"
        )
    
    return {
        "checkout_url": checkout_url
    }

@router.post("/cancel", response_model=dict)
def cancel_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Cancel the current user's subscription
    """
    # Get the active subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    # Cancel subscription
    success = payment_service.cancel_subscription(db, subscription)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )
    
    return {
        "message": "Subscription canceled successfully"
    }

@router.get("/usage", response_model=UsageBalance)
def get_usage_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get the current user's token usage balance
    """
    # Get the active subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    # Get usage balance
    usage_balance = payment_service.get_usage_balance(subscription)
    
    return usage_balance

@router.get("/billing-portal", response_model=dict)
def get_billing_portal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get a URL for the Stripe billing portal
    """
    # Get the active subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    # Create billing portal session
    portal_url = payment_service.create_billing_portal_session(
        subscription.stripe_customer_id
    )
    
    if not portal_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )
    
    return {
        "portal_url": portal_url
    }
