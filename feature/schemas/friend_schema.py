# feature/schemas/friend_schema.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.response import SuccessResponse

class UserBasicInfo(BaseModel):
    id: int
    name: Optional[str] = None
    profile_picture_url: Optional[str] = None

class FriendRequestCreate(BaseModel):
    receiver_id: int = Field(..., description="ID of the user to send friend request to")

class BlockUserRequest(BaseModel):
    user_id: int = Field(..., description="ID of the user to block")
    reason: Optional[str] = Field(None, max_length=255)

class FriendRequestInfo(BaseModel):
    id: str
    requester: UserBasicInfo
    receiver: UserBasicInfo
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class FriendRequestResponse(SuccessResponse[FriendRequestInfo]):
    """Response model for single friend request operations"""
    pass

class FriendRequestListResponse(SuccessResponse[List[FriendRequestInfo]]):
    """Response model for list of friend requests"""
    pass

class BlockedUserInfo(BaseModel):
    id: str
    blocked_user: UserBasicInfo
    reason: Optional[str]
    blocked_at: datetime

    class Config:
        from_attributes = True

class BlockedUserResponse(SuccessResponse[BlockedUserInfo]):
    """Response model for block user operations"""
    pass

class BlockedUserListResponse(SuccessResponse[List[BlockedUserInfo]]):
    """Response model for list of blocked users"""
    pass