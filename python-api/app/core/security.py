from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings
import time
from collections import defaultdict

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password
    """
    return pwd_context.hash(password)

# Rate limiting implementation
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Track request counts per API key with time window
        self.request_counts = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for non-API routes
        path = request.url.path
        if not path.startswith("/api"):
            return await call_next(request)
        
        # Get API key from header or query parameter
        api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        
        if not api_key:
            # No API key - apply default rate limit
            max_requests = settings.RATE_LIMIT_DEFAULT
        else:
            # TODO: Get user's subscription tier from database
            # For now, using a placeholder implementation
            if api_key.startswith("test_"):
                max_requests = settings.RATE_LIMIT_FREE_TIER
            elif api_key.startswith("starter_"):
                max_requests = settings.RATE_LIMIT_STARTER
            elif api_key.startswith("pro_"):
                max_requests = settings.RATE_LIMIT_PRO
            elif api_key.startswith("enterprise_"):
                max_requests = settings.RATE_LIMIT_ENTERPRISE
            else:
                max_requests = settings.RATE_LIMIT_DEFAULT
        
        # Current time
        now = time.time()
        
        # Clean up old requests (older than 1 minute)
        self.request_counts[api_key] = [
            timestamp for timestamp in self.request_counts[api_key]
            if now - timestamp < 60
        ]
        
        # Check if rate limit exceeded
        if len(self.request_counts[api_key]) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        
        # Add current request timestamp
        self.request_counts[api_key].append(now)
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max_requests - len(self.request_counts[api_key])
        response.headers["X-Rate-Limit-Limit"] = str(max_requests)
        response.headers["X-Rate-Limit-Remaining"] = str(remaining)
        response.headers["X-Rate-Limit-Reset"] = str(int(now + 60))
        
        return response
