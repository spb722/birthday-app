from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status  # Add this explicit import
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from sqlalchemy.orm import Session
from datetime import datetime,date
from app.core.database import get_db_dependency
from app.api.deps import get_current_user
from app.core.error_handler import create_success_response
from app.models.user import User
from app.schemas.response import SuccessResponse
from ..services.room_service import RoomService
from typing import Optional, List
from fastapi import status
from ..schemas.room_schema import (
    RoomCreate,
    RoomUpdate,
    RoomResponse,
    RoomListResponse,
    RoomFilter,
    RoomStatsResponse,
    ParticipantUpdate, RoomInvitation, ParticipantListResponse
)

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("/invitations", response_model=RoomListResponse)
async def get_pending_invitations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Get list of rooms where the user has pending invitations."""
    try:
        result = await RoomService.get_pending_invitations(
            db,
            current_user.id,
            page,
            page_size
        )

        return create_success_response(
            message="Pending invitations retrieved successfully",
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
@router.get("/{room_id}/join-requests", response_model=ParticipantListResponse)
async def get_pending_join_requests(
    room_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Get a list of users who have requested to join the room."""
    try:
        result = await RoomService.get_pending_join_requests(
            db,
            room_id,
            current_user.id,
            page,
            page_size
        )

        return create_success_response(
            message="Pending join requests retrieved successfully",
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
@router.post("", response_model=RoomResponse)
async def create_room(
        request: RoomCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db_dependency)
):
    """Create a new room with enhanced validation."""
    try:
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

        # Ensure participants are loaded
        room.participants = []  # Initialize empty list if none exist

        return create_success_response(
            message=message,
            data=room
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating room: {str(e)}"
        )
@router.get("", response_model=RoomListResponse)
async def list_rooms(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    query: Optional[str] = Query(None, min_length=1, max_length=100),
    room_type: Optional[List[str]] = Query(None),
    status: Optional[List[str]] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    birthday_from_date: Optional[date] = Query(None, description="Filter by celebrant birthday from date"),
    birthday_to_date: Optional[date] = Query(None, description="Filter by celebrant birthday to date"),
    is_archived: Optional[bool] = Query(False),
    friends_only: Optional[bool] = Query(False, description="Filter to show only rooms created by friends"),
    my_rooms: Optional[bool] = Query(False, description="Show only rooms where I'm owner or participant"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """List rooms with advanced filtering and pagination."""
    filter_params = RoomFilter(
        query=query,
        room_type=room_type,
        status=status,
        from_date=from_date,
        to_date=to_date,
        birthday_from_date=birthday_from_date,
        birthday_to_date=birthday_to_date,
        is_archived=is_archived,
        friends_only=friends_only,
        my_rooms=my_rooms
    )

    try:
        result = await RoomService.list_rooms(
            db,
            current_user.id,
            filter_params,
            page,
            page_size
        )

        return create_success_response(
            message="Rooms retrieved successfully",
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Get detailed room information."""
    room = await RoomService.get_room_by_id(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # Update participant activity
    await RoomService.update_participant_activity(db, room_id, current_user.id)

    return create_success_response(
        message="Room details retrieved successfully",
        data=room
    )

@router.get("/{room_id}/stats", response_model=RoomStatsResponse)
async def get_room_stats(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Get room statistics."""
    stats = await RoomService.get_room_stats(db, room_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    return create_success_response(
        message="Room statistics retrieved successfully",
        data=stats
    )

@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: str,
    request: RoomUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Update room settings."""
    success, message, room = await RoomService.update_room(
        db,
        room_id,
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
@router.post("/{room_id}/activate", response_model=RoomResponse)
async def activate_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """
    Activate a room. Only the room owner can activate their room.
    """
    success, message, room = await RoomService.activate_room(
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

@router.post("/{room_id}/invite", response_model=RoomResponse)
async def invite_users(
    room_id: str,
    invitation: RoomInvitation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Invite users to a room."""
    success, message, room = await RoomService.invite_users(
        db,
        room_id,
        current_user.id,
        invitation.user_ids,
        invitation.message
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

@router.post("/{room_id}/archive", response_model=RoomResponse)
async def archive_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Archive a room (soft delete)."""
    success, message, room = await RoomService.archive_room(
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

@router.post("/{room_id}/participants/bulk", response_model=RoomResponse)
async def bulk_update_participants(
    room_id: str,
    user_ids: List[int],
    action: str = Query(..., pattern="^(approve|reject|ban)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Bulk update participant statuses."""
    success, message, result = await RoomService.bulk_update_participants(
        db,
        room_id,
        current_user.id,
        user_ids,
        action
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return create_success_response(
        message=message,
        data=result
    )

@router.post("/{room_id}/join", response_model=RoomResponse)
async def join_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Request to join a room."""
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
    """Update individual participant status."""
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