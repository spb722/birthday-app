# feature/schemas/contact_schema.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from app.schemas.response import SuccessResponse

class ContactInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone_number: str = Field(..., pattern=r'^\+?1?\d{9,15}$', description="Phone number in E.164 format")

    @field_validator('phone_number')
    def validate_phone_number(cls, value):
        """Validate phone number format."""
        import re
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise ValueError('Invalid phone number format. Must be E.164 format.')
        return value

class ContactSyncRequest(BaseModel):
    contacts: List[ContactInfo] = Field(..., description="List of contacts to sync")

class UserMatchInfo(BaseModel):
    contact_name: str = Field(..., description="Name from phone contacts")
    user_id: str = Field(..., description="Matched user's ID")
    profile_picture: Optional[str] = Field(None, description="User's profile picture URL")
    mutual_friends: int = Field(default=0, description="Number of mutual connections")

class ContactSyncResponse(SuccessResponse[List[UserMatchInfo]]):
    """Response model for contact sync results"""