from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class AIModelBase(BaseModel):
    name: str
    type: str
    description: str
    version: str
    file_path: str
    token_multiplier: float = 1.0

class AIModelCreate(AIModelBase):
    pass

class AIModelRead(AIModelBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TextGenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

class TextGenerationResponse(BaseModel):
    text: str
    tokens_used: int
    model: str

class ImageGenerationRequest(BaseModel):
    prompt: str
    width: int = 512
    height: int = 512
    num_inference_steps: int = 50
    guidance_scale: float = 7.5

class ImageGenerationResponse(BaseModel):
    image_url: str
    tokens_used: int
    model: str
