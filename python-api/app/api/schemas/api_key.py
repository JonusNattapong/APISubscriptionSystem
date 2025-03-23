from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ApiKeyBase(BaseModel):
    name: str
    
class ApiKeyCreate(ApiKeyBase):
    expires_at: Optional[datetime] = None

class ApiKeyRead(ApiKeyBase):
    id: int
    key: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
