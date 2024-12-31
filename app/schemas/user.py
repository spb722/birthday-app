from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    phone: Optional[str] = None
    email_verified: Optional[str] = "unverified"
    phone_verified: Optional[str] = "unverified"
    account_status: Optional[str] = "unregistered"
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    phone: Optional[str] = None
    email_verified: Optional[str] = None
    phone_verified: Optional[str] = None
    account_status: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

# Auth related schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: Optional[str] = None

# Response schemas
class UserResponse(User):
    pass

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class PayloadResponse(BaseModel):
    user: UserResponse
    auth: AuthResponse

class TokenResponse(BaseModel):
    status: str
    message: str
    payload: PayloadResponse