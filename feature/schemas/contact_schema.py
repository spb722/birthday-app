# feature/schemas/contact_schema.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.response import SuccessResponse

class ContactInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone_number: str

class ContactSyncRequest(BaseModel):
    contacts: List[ContactInfo] = Field(..., description="List of contacts to sync")

class UserMatchInfo(BaseModel):
    contact_name: str = Field(..., description="Name from phone contacts")
    user_id: str = Field(..., description="Matched user's ID")
    profile_picture: Optional[str] = Field(None, description="User's profile picture URL")
    mutual_friends: int = Field(default=0, description="Number of mutual connections")
    matched_phone: str = Field(..., description="Phone number of the matched user")
    input_phone: str = Field(..., description="Phone number provided for matching")
    first_name: str = Field(..., description="First name of the matched user")

class ContactSyncResponse(SuccessResponse[List[UserMatchInfo]]):
    """Response model for contact sync results"""