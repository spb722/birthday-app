from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db_dependency
from app.api.deps import get_current_user
from app.core.error_handler import create_success_response
from app.models.user import User
from ..services.room_service import RoomService
from typing import Optional
from ..schemas.room_schema import (
    RoomCreate,
    RoomUpdate,
    ParticipantUpdate,
    RoomInvitation,
    InvitationResponse,
    RoomResponse,
    RoomListResponse
)

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.post("", response_model=RoomResponse)
async def create_room(
    request: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Create a new room"""
    success, message, room = await RoomService.create_room(
        db,
        current_user.id,
        request
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return create_success_response(
        message=message,
        data=room
    )

@router.get("", response_model=RoomListResponse)
async def list_rooms(
    room_type: str = Query(..., pattern="^(my_rooms|upcoming)$"),
    status: Optional[str] = Query(None, pattern="^(pending|active|expired)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """List rooms based on filters"""
    rooms = await RoomService.list_rooms(
        db,
        current_user.id,
        room_type,
        status,
        skip,
        limit
    )

    return create_success_response(
        message="Rooms retrieved successfully",
        data=rooms
    )

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Get specific room details"""
    room = await RoomService.get_room_by_id(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    return create_success_response(
        message="Room details retrieved successfully",
        data=room
    )

@router.post("/{room_id}/join", response_model=RoomResponse)
async def join_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Request to join a room"""
    success, message, room = await RoomService.join_room(
        db,
        room_id,
        current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return create_success_response(
        message=message,
        data=room
    )

@router.put("/{room_id}/participants/{user_id}", response_model=RoomResponse)
async def update_participant(
    room_id: str,
    user_id: int,
    request: ParticipantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Update participant status"""
    success, message, room = await RoomService.update_participant(
        db,
        room_id,
        current_user.id,
        user_id,
        request.status
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return create_success_response(
        message=message,
        data=room
    )

@router.post("/{room_id}/invitations", response_model=RoomResponse)
async def send_invitations(
    room_id: str,
    request: RoomInvitation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Send room invitations"""
    success, message, room = await RoomService.send_invitations(
        db,
        room_id,
        current_user.id,
        request.user_ids
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return create_success_response(
        message=message,
        data=room
    )

@router.put("/invitations/{invitation_id}", response_model=RoomResponse)
async def respond_to_invitation(
    invitation_id: str,
    request: InvitationResponse,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Accept or reject room invitation"""
    success, message, room = await RoomService.handle_invitation(
        db,
        invitation_id,
        current_user.id,
        request.status
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return create_success_response(
        message=message,
        data=room
    )

@router.delete("/{room_id}")
async def delete_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Delete a room"""
    success, message = await RoomService.delete_room(
        db,
        room_id,
        current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return create_success_response(
        message=message,
        data=None
    )