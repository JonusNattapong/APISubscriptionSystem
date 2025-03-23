from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import secrets
import string
from datetime import datetime, timedelta

from app.db.base import get_db
from app.models.user import User, ApiKey
from app.api.schemas.api_key import ApiKeyCreate, ApiKeyRead
from app.api.dependencies import get_current_user, get_current_active_user

router = APIRouter()

def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure API key
    """
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return api_key

@router.get("/", response_model=List[ApiKeyRead])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    List all API keys for the current user
    """
    api_keys = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id
    ).all()
    
    return api_keys

@router.post("/", response_model=ApiKeyRead)
def create_api_key(
    api_key_in: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new API key for the current user
    """
    # Check if user has an active subscription
    # This is a placeholder - in a real application, you would check the subscription status
    has_subscription = True
    
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required to create API keys"
        )
    
    # Check if user has reached the maximum number of API keys
    # This is a placeholder - in a real application, you would set limits per subscription tier
    max_api_keys = 5
    current_api_keys = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.is_active == True
    ).count()
    
    if current_api_keys >= max_api_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum number of API keys ({max_api_keys}) reached"
        )
    
    # Generate a new API key
    key = generate_api_key()
    
    # Set expiration date if provided, otherwise default to 1 year
    expires_at = api_key_in.expires_at
    if not expires_at:
        expires_at = datetime.utcnow() + timedelta(days=365)
    
    # Create API key
    api_key = ApiKey(
        user_id=current_user.id,
        key=key,
        name=api_key_in.name,
        expires_at=expires_at
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return api_key

@router.delete("/{api_key_id}", response_model=dict)
def delete_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Delete (deactivate) an API key
    """
    # Get the API key
    api_key = db.query(ApiKey).filter(
        ApiKey.id == api_key_id,
        ApiKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Deactivate the API key
    api_key.is_active = False
    db.commit()
    
    return {
        "message": "API key deactivated successfully"
    }

@router.post("/{api_key_id}/renew", response_model=ApiKeyRead)
def renew_api_key(
    api_key_id: int,
    expiration_days: int = 365,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Renew an API key with a new expiration date
    """
    # Get the API key
    api_key = db.query(ApiKey).filter(
        ApiKey.id == api_key_id,
        ApiKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Set new expiration date
    api_key.expires_at = datetime.utcnow() + timedelta(days=expiration_days)
    api_key.is_active = True
    
    db.commit()
    db.refresh(api_key)
    
    return api_key
