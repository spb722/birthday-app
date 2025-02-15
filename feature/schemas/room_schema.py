from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.response import SuccessResponse
from ..schemas.friend_schema import UserBasicInfo  # Updated import

class RoomCreate(BaseModel):
    room_name: str = Field(..., min_length=1, max_length=255)
    privacy_type: str = Field(..., pattern="^(public|private)$")
    activation_time: datetime
    expiration_time: datetime

class RoomUpdate(BaseModel):
    room_name: Optional[str] = Field(None, min_length=1, max_length=255)
    privacy_type: Optional[str] = Field(None, pattern="^(public|private)$")
    status: Optional[str] = Field(None, pattern="^(pending|active|expired)$")

class ParticipantUpdate(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected|banned)$")

class RoomInvitation(BaseModel):
    user_ids: List[int] = Field(..., min_items=1)

class InvitationResponse(BaseModel):
    status: str = Field(..., pattern="^(accepted|rejected)$")

class RoomParticipantInfo(BaseModel):
    user: UserBasicInfo
    is_admin: bool
    status: str
    joined_at: datetime

    class Config:
        from_attributes = True

class RoomInfo(BaseModel):
    id: str
    room_name: str
    privacy_type: str
    status: str
    owner: UserBasicInfo
    activation_time: datetime
    expiration_time: datetime
    created_at: datetime
    participants: List[RoomParticipantInfo]

    class Config:
        from_attributes = True

# Response Models
class RoomResponse(SuccessResponse[RoomInfo]):
    """Response model for single room operations"""
    pass

class RoomListResponse(SuccessResponse[List[RoomInfo]]):
    """Response model for list of rooms"""
    pass