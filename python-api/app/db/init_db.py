import logging
from sqlalchemy.orm import Session

from app.db.base import Base, engine
from app.models.user import User, SubscriptionPlan, AIModel
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

# Create initial subscription plans
INITIAL_PLANS = [
    {
        "name": "Starter",
        "description": "Basic plan with limited usage",
        "price": 10.0,
        "token_limit": 10000,
        "rate_limit": 50,
        "stripe_price_id": "price_starter"
    },
    {
        "name": "Pro",
        "description": "Professional plan with higher limits",
        "price": 50.0,
        "token_limit": 100000,
        "rate_limit": 200,
        "stripe_price_id": "price_pro"
    },
    {
        "name": "Enterprise",
        "description": "Enterprise plan with maximum limits",
        "price": 200.0,
        "token_limit": 500000,
        "rate_limit": 1000,
        "stripe_price_id": "price_enterprise"
    }
]

# Create initial AI models
INITIAL_MODELS = [
    {
        "name": "Mistral-7B",
        "type": "text",
        "description": "Mistral 7B language model for text generation",
        "version": "1.0",
        "file_path": "models/mistral-7b",
        "token_multiplier": 1.0
    },
    {
        "name": "Llama-2-70B",
        "type": "text",
        "description": "Llama 2 70B language model for advanced text generation",
        "version": "1.0",
        "file_path": "models/llama-2-70b",
        "token_multiplier": 2.0
    },
    {
        "name": "Stable-Diffusion-XL",
        "type": "image",
        "description": "Stable Diffusion XL for high-quality image generation",
        "version": "1.0",
        "file_path": "models/stable-diffusion-xl",
        "token_multiplier": 5.0
    },
    {
        "name": "Whisper-Large",
        "type": "audio",
        "description": "Whisper Large model for speech recognition and transcription",
        "version": "1.0",
        "file_path": "models/whisper-large",
        "token_multiplier": 3.0
    }
]

def init_db(db: Session) -> None:
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create initial subscription plans
    for plan_data in INITIAL_PLANS:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == plan_data["name"]).first()
        if not plan:
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)
            logger.info(f"Created subscription plan: {plan_data['name']}")
    
    # Create initial AI models
    for model_data in INITIAL_MODELS:
        model = db.query(AIModel).filter(AIModel.name == model_data["name"]).first()
        if not model:
            model = AIModel(**model_data)
            db.add(model)
            logger.info(f"Created AI model: {model_data['name']}")
    
    # Create admin user if it doesn't exist
    admin_user = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin_user:
        admin_user = User(
            email="admin@example.com",
            username="admin",
            hashed_password=get_password_hash("admin"),
            is_active=True,
            is_admin=True
        )
        db.add(admin_user)
        logger.info("Created admin user")
    
    db.commit()
    logger.info("Database initialized")
