from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class SubscriptionPlanBase(BaseModel):
    name: str
    description: str
    price: float
    token_limit: int
    rate_limit: int

class SubscriptionPlanCreate(SubscriptionPlanBase):
    stripe_price_id: str

class SubscriptionPlanRead(SubscriptionPlanBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SubscriptionBase(BaseModel):
    plan_id: int

class SubscriptionCreate(SubscriptionBase):
    user_id: int

class SubscriptionRead(SubscriptionBase):
    id: int
    user_id: int
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: datetime
    updated_at: datetime
    plan: SubscriptionPlanRead

    class Config:
        orm_mode = True

class UsageBalance(BaseModel):
    total_tokens: int
    used_tokens: int
    remaining_tokens: int
    usage_percentage: float
