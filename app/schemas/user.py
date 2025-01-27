from pydantic import BaseModel, EmailStr ,Field
from typing import Optional
from datetime import datetime
from app.schemas.response import SuccessResponse
from datetime import date
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email:Optional[EmailStr] = None
    # name: Optional[str] = None
    first_name: Optional[str] = None    # Replace name with first_name
    last_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    phone: Optional[str] = None
    email_verified: Optional[str] = "unverified"
    phone_verified: Optional[str] = "unverified"
    account_status: Optional[str] = "unregistered"
    is_active: Optional[bool] = True
    date_of_birth: Optional[date] = None
class UserCreate(UserBase):
    password: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None  # Replace name with first_name
    last_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    phone: Optional[str] = None
    email_verified: Optional[str] = None
    phone_verified: Optional[str] = None
    account_status: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)
    date_of_birth: Optional[date] = None

class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserResponse(SuccessResponse[User]):
    pass

class AuthData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class PayloadData(BaseModel):
    user: User
    auth: AuthData

class AuthResponse(SuccessResponse[PayloadData]):
    pass