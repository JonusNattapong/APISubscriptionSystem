from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    status = Column(String)  # active, canceled, expired, etc.
    stripe_subscription_id = Column(String, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)  # e.g. "Starter", "Pro", "Enterprise"
    description = Column(String)
    price = Column(Float)  # Monthly price in USD
    token_limit = Column(Integer)  # e.g. 10,000 tokens per month
    rate_limit = Column(Integer)  # Requests per minute
    stripe_price_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    key = Column(String, unique=True, index=True)
    name = Column(String)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    endpoint = Column(String)  # e.g. "/api/v1/models/text-generation"
    model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=True)
    tokens_used = Column(Integer)  # Number of tokens used in this request
    request_data = Column(String, nullable=True)  # JSON string of request data
    status_code = Column(Integer)  # HTTP status code
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="usage_logs")
    model = relationship("AIModel", back_populates="usage_logs")

class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)  # e.g. "Mistral-7B", "Llama-2-70B"
    type = Column(String)  # e.g. "text", "image", "audio"
    description = Column(String)
    version = Column(String)
    file_path = Column(String)  # Path to the model file
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Pricing and limits
    token_multiplier = Column(Float, default=1.0)  # Cost multiplier for this model
    
    # Relationships
    usage_logs = relationship("UsageLog", back_populates="model")
