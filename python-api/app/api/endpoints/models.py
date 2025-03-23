from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import base64
import os

from app.db.base import get_db
from app.models.user import AIModel, User, UsageLog
from app.api.schemas.model import (
    AIModelRead,
    TextGenerationRequest,
    TextGenerationResponse,
    ImageGenerationRequest,
    ImageGenerationResponse
)
from app.services.model_service import model_service
from app.api.dependencies import get_current_user, get_current_active_user, verify_api_key

router = APIRouter()

@router.get("/", response_model=List[AIModelRead])
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve all available AI models
    """
    models = db.query(AIModel).filter(AIModel.is_active == True).all()
    return models

@router.get("/available", response_model=List[dict])
def list_available_models(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve all available models that can be loaded
    """
    return model_service.get_available_models()

@router.post("/text-generation", response_model=TextGenerationResponse)
def generate_text(
    request: TextGenerationRequest,
    model_name: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> Any:
    """
    Generate text using an AI model
    """
    # Get the model
    model = db.query(AIModel).filter(
        AIModel.name == model_name,
        AIModel.is_active == True,
        AIModel.type == "text"
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text generation model '{model_name}' not found"
        )
    
    # Get user from API key
    user = api_key.user
    
    # Check if user has an active subscription with sufficient tokens
    # This is a placeholder - you would implement actual subscription checking
    has_subscription = True
    
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required for text generation"
        )
    
    # Generate text
    generated_text = model_service.generate_text(
        model_name,
        request.prompt,
        max_tokens=request.max_tokens
    )
    
    if not generated_text:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Text generation failed"
        )
    
    # Calculate tokens used (placeholder - would be more accurate in real implementation)
    tokens_used = len(request.prompt.split()) + len(generated_text.split())
    
    # Log usage
    usage_log = UsageLog(
        user_id=user.id,
        api_key_id=api_key.id,
        endpoint="/api/models/text-generation",
        model_id=model.id,
        tokens_used=tokens_used,
        request_data=request.json(),
        status_code=200
    )
    db.add(usage_log)
    db.commit()
    
    return {
        "text": generated_text,
        "tokens_used": tokens_used,
        "model": model_name
    }

@router.post("/image-generation", response_model=ImageGenerationResponse)
def generate_image(
    request: ImageGenerationRequest,
    model_name: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> Any:
    """
    Generate an image using a Stable Diffusion model
    """
    # Get the model
    model = db.query(AIModel).filter(
        AIModel.name == model_name,
        AIModel.is_active == True,
        AIModel.type == "image"
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image generation model '{model_name}' not found"
        )
    
    # Get user from API key
    user = api_key.user
    
    # Check if user has an active subscription with sufficient tokens
    # This is a placeholder - you would implement actual subscription checking
    has_subscription = True
    
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required for image generation"
        )
    
    # Generate image
    image_bytes = model_service.generate_image(
        model_name,
        request.prompt
    )
    
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image generation failed"
        )
    
    # Save image to disk (in a real app, you might use cloud storage)
    os.makedirs("static/images", exist_ok=True)
    image_filename = f"image_{user.id}_{int(time.time())}.png"
    image_path = f"static/images/{image_filename}"
    
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    
    # Calculate tokens used for image generation (placeholder)
    tokens_used = 1000  # Image generation typically costs more tokens
    
    # Log usage
    usage_log = UsageLog(
        user_id=user.id,
        api_key_id=api_key.id,
        endpoint="/api/models/image-generation",
        model_id=model.id,
        tokens_used=tokens_used,
        request_data=request.json(),
        status_code=200
    )
    db.add(usage_log)
    db.commit()
    
    # Return image URL
    image_url = f"/static/images/{image_filename}"
    
    return {
        "image_url": image_url,
        "tokens_used": tokens_used,
        "model": model_name
    }

@router.get("/image/{filename}")
def get_image(
    filename: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> Any:
    """
    Retrieve a generated image
    """
    image_path = f"static/images/{filename}"
    
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    return Response(content=image_bytes, media_type="image/png")
