# feature/controllers/friend_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from ..schemas.friend_schema import (
    FriendRequestCreate,
    BlockUserRequest,
    FriendRequestResponse,
    FriendRequestListResponse,
    BlockedUserResponse,
    BlockedUserListResponse,
FriendListResponse
)
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db_dependency
from app.api.deps import get_current_user
from app.core.error_handler import create_success_response
from ..services.friend_service import FriendService
from ..schemas.friend_schema import FriendListResponse
router = APIRouter(tags=["friends"])
friend_service = FriendService()


@router.get("/friends", response_model=FriendListResponse)
async def get_friends(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """
    Get list of current user's friends
    """
    friends = await friend_service.get_friends(
        db,
        current_user.id,
        skip,
        limit
    )

    return create_success_response(
        message="Friends retrieved successfully",
        data=friends
    )

@router.post("/friends/request", response_model=FriendRequestResponse)
async def create_friend_request(
        request: FriendRequestCreate,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db_dependency)
):
    """
    Create a new friend request
    """
    success, message, friend_request = await friend_service.create_friend_request(
        db,
        current_user.id,
        request.receiver_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return create_success_response(
        message=message,
        data=friend_request
    )


@router.get("/friends/requests/incoming", response_model=FriendRequestListResponse)
async def get_incoming_requests(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db_dependency)
):
    """
    Get list of incoming friend requests
    """
    requests = await friend_service.get_incoming_requests(
        db,
        current_user.id,
        skip,
        limit
    )

    return create_success_response(
        message="Incoming friend requests retrieved successfully",
        data=requests
    )


@router.get("/friends/requests/outgoing", response_model=FriendRequestListResponse)
async def get_outgoing_requests(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db_dependency)
):
    """
    Get list of outgoing friend requests
    """
    requests = await friend_service.get_outgoing_requests(
        db,
        current_user.id,
        skip,
        limit
    )

    return create_success_response(
        message="Outgoing friend requests retrieved successfully",
        data=requests
    )


@router.put("/friends/requests/{request_id}/accept", response_model=FriendRequestResponse)
async def accept_friend_request(
        request_id: str,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db_dependency)
):
    """
    Accept a friend request
    """
    success, message, updated_request = await friend_service.handle_friend_request(
        db,
        request_id,
        current_user.id,
        "accept"
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return create_success_response(
        message=message,
        data=updated_request
    )


@router.put("/friends/requests/{request_id}/decline", response_model=FriendRequestResponse)
async def decline_friend_request(
        request_id: str,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db_dependency)
):
    """
    Decline a friend request
    """
    success, message, updated_request = await friend_service.handle_friend_request(
        db,
        request_id,
        current_user.id,
        "decline"
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return create_success_response(
        message=message,
        data=updated_request
    )


@router.delete("/friends/requests/{request_id}")
async def cancel_friend_request(
        request_id: str,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db_dependency)
):
    """
    Cancel a sent friend request
    """
    success, message = await friend_service.cancel_friend_request(
        db,
        request_id,
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


@router.post("/friends/block", response_model=BlockedUserResponse)
async def block_user(
        request: BlockUserRequest,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db_dependency)
):
    """
    Block a user
    """
    success, message, blocked = await friend_service.block_user(
        db,
        current_user.id,
        request.user_id,
        request.reason
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return create_success_response(
        message=message,
        data=blocked
    )


@router.delete("/friends/block/{user_id}")
async def unblock_user(
        user_id: int,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db_dependency)
):
    """
    Unblock a user
    """
    success, message = await friend_service.unblock_user(
        db,
        current_user.id,
        user_id
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