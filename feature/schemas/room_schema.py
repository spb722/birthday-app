from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.response import SuccessResponse
from ..schemas.friend_schema import UserBasicInfo
from ..models.room import RoomStatus, RoomPrivacy, RoomType

# Base Schema for Room Fields
class RoomBase(BaseModel):
    room_name: str = Field(..., min_length=1, max_length=255, description="Name of the room")
    description: Optional[str] = Field(None, max_length=1000, description="Room description")
    room_type: RoomType = Field(default=RoomType.EVENT, description="Type of room")
    privacy_type: RoomPrivacy = Field(default=RoomPrivacy.PRIVATE, description="Privacy setting")
    max_participants: Optional[int] = Field(None, gt=0, le=1000, description="Maximum number of participants")
    auto_approve_participants: bool = Field(default=False, description="Auto approve new participants")

# Create Room Request
class RoomCreate(RoomBase):
    activation_time: datetime = Field(..., description="Room activation time")
    expiration_time: datetime = Field(..., description="Room expiration time")
    metadata: Optional[Dict[str, Any]] = Field(default=dict(), description="Additional room metadata")

    @validator('expiration_time')
    def validate_expiration_time(cls, v, values):
        if 'activation_time' in values and v <= values['activation_time']:
            raise ValueError('Expiration time must be after activation time')
        return v

    @validator('activation_time')
    def validate_activation_time(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Activation time must be in the future')
        return v

# Update Room Request
class RoomUpdate(BaseModel):
    room_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    privacy_type: Optional[RoomPrivacy] = None
    max_participants: Optional[int] = Field(None, gt=0, le=1000)
    auto_approve_participants: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

# Participant Related Schemas
class ParticipantUpdate(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected|banned)$")

class RoomInvitation(BaseModel):
    user_ids: List[int] = Field(..., min_items=1, max_items=100)
    message: Optional[str] = Field(None, max_length=500)

class InvitationResponse(BaseModel):
    status: str = Field(..., pattern="^(accepted|rejected)$")

# Response Schemas
class RoomParticipantInfo(BaseModel):
    user: UserBasicInfo
    is_admin: bool
    status: str
    joined_at: datetime
    last_active_at: Optional[datetime]

    class Config:
        from_attributes = True

class RoomInfo(BaseModel):
    id: str
    room_name: str
    description: Optional[str]
    room_type: RoomType
    privacy_type: RoomPrivacy
    status: RoomStatus
    owner: UserBasicInfo
    max_participants: Optional[int]
    auto_approve_participants: bool
    is_archived: bool
    activation_time: datetime
    expiration_time: datetime
    last_activity: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    metadata: Dict[str, Any]
    participants: List[RoomParticipantInfo]
    participant_count: int

    class Config:
        from_attributes = True

    @validator('participant_count', pre=True, always=True)
    def set_participant_count(cls, v, values):
        return len(values.get('participants', []))

# Room Stats Schema
class RoomStats(BaseModel):
    total_participants: int
    active_participants: int
    pending_requests: int
    last_activity: Optional[datetime]
    capacity_used: float  # percentage

# List Response for Rooms with Pagination
class PaginatedResponse(BaseModel):
    items: List[RoomInfo]
    total: int
    page: int
    size: int
    pages: int

# Response Models
class RoomResponse(SuccessResponse[RoomInfo]):
    """Response model for single room operations"""
    pass

class RoomListResponse(SuccessResponse[PaginatedResponse]):
    """Response model for list of rooms with pagination"""
    pass

class RoomStatsResponse(SuccessResponse[RoomStats]):
    """Response model for room statistics"""
    pass

# Search/Filter Schema
class RoomFilter(BaseModel):
    query: Optional[str] = Field(None, min_length=1, max_length=100)
    room_type: Optional[List[RoomType]] = None
    privacy_type: Optional[List[RoomPrivacy]] = None
    status: Optional[List[RoomStatus]] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    owner_id: Optional[int] = None
    is_archived: Optional[bool] = None