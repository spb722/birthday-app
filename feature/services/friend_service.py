# feature/services/friend_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, String
from typing import List, Optional, Tuple
from ..repository.friend_repository import FriendRepository
from ..models.friend import FriendRequest, BlockedUser, FriendRequestStatus
from ..models.room import Room, RoomPrivacy
from app.models.user import User
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from ..repository.friend_repository import FriendRepository
from ..schemas.friend_schema import (
    FriendInfo,
    FriendRequestInfo,
    BlockedUserInfo,
    FriendListResponse
)
from ..models.friend import FriendRequest, BlockedUser, FriendRequestStatus
from app.models.user import User

class FriendService:
    def __init__(self):
        self.repository = FriendRepository()

    async def create_friend_request(
            self,
            db: Session,
            requester_id: int,
            receiver_id: int
    ) -> Tuple[bool, str, Optional[FriendRequest]]:
        try:
            # Check if users exist
            receiver = db.query(User).filter(User.id == receiver_id).first()
            if not receiver:
                return False, "Receiver not found", None

            # Check if user is trying to friend themselves
            if requester_id == receiver_id:
                return False, "Cannot send friend request to yourself", None

            # Check if already blocked
            is_blocked = await self.repository.is_blocked(db, requester_id, receiver_id)
            if is_blocked:
                return False, "Cannot send friend request to this user", None

            # Check for existing pending request
            existing_request = await self.repository.get_existing_request(
                db, requester_id, receiver_id
            )
            if existing_request:
                return False, "Friend request already sent", None

            # Create friend request
            friend_request = await self.repository.create_friend_request(
                db, requester_id, receiver_id
            )

            return True, "Friend request sent successfully", friend_request

        except Exception as e:
            db.rollback()
            return False, f"Error creating friend request: {str(e)}", None

    async def get_incoming_requests(
            self,
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 10
    ) -> List[FriendRequest]:
        try:
            requests = await self.repository.get_incoming_requests(db, user_id, skip, limit)
            # Validate that requester data is loaded
            for request in requests:
                if not request.requester:
                    # Log or handle missing requester
                    print(f"Warning: Missing requester for request {request.id}")
            return requests
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error fetching incoming requestss: {str(e)}")

    async def get_outgoing_requests(
            self,
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 10
    ) -> List[FriendRequest]:
        return await self.repository.get_outgoing_requests(db, user_id, skip, limit)

    async def handle_friend_request(
            self,
            db: Session,
            request_id: str,
            user_id: int,
            action: str
    ) -> Tuple[bool, str, Optional[FriendRequest]]:
        try:
            request = await self.repository.get_friend_request(db, request_id)
            if not request:
                return False, "Friend request not found", None

            if request.receiver_id != user_id:
                return False, "Not authorized to handle this request", None

            if request.status != FriendRequestStatus.PENDING:
                return False, "Request is not pending", None

            status = FriendRequestStatus.ACCEPTED if action == "accept" else FriendRequestStatus.DECLINED
            updated_request = await self.repository.update_request_status(db, request, status)

            action_text = "accepted" if action == "accept" else "declined"
            return True, f"Friend request {action_text} successfully", updated_request

        except Exception as e:
            db.rollback()
            return False, f"Error handling friend request: {str(e)}", None

    async def cancel_friend_request(
            self,
            db: Session,
            request_id: str,
            user_id: int
    ) -> Tuple[bool, str]:
        try:
            request = await self.repository.get_friend_request(db, request_id)
            if not request:
                return False, "Friend request not found"

            if request.requester_id != user_id:
                return False, "Not authorized to cancel this request"

            if request.status != FriendRequestStatus.PENDING:
                return False, "Request cannot be canceled"

            await self.repository.update_request_status(
                db, request, FriendRequestStatus.CANCELED
            )
            return True, "Friend request canceled successfully"

        except Exception as e:
            db.rollback()
            return False, f"Error canceling friend request: {str(e)}"

    async def block_user(
            self,
            db: Session,
            blocker_id: int,
            blocked_id: int,
            reason: Optional[str] = None
    ) -> Tuple[bool, str, Optional[BlockedUser]]:
        try:
            # Check if user exists
            blocked_user = db.query(User).filter(User.id == blocked_id).first()
            if not blocked_user:
                return False, "User not found", None

            # Check if trying to block themselves
            if blocker_id == blocked_id:
                return False, "Cannot block yourself", None

            # Check if already blocked
            is_blocked = await self.repository.is_blocked(db, blocker_id, blocked_id)
            if is_blocked:
                return False, "User is already blocked", None

            # Block user
            blocked = await self.repository.block_user(
                db, blocker_id, blocked_id, reason
            )

            return True, "User blocked successfully", blocked

        except Exception as e:
            db.rollback()
            return False, f"Error blocking user: {str(e)}", None

    async def unblock_user(
            self,
            db: Session,
            blocker_id: int,
            blocked_id: int
    ) -> Tuple[bool, str]:
        try:
            if blocker_id == blocked_id:
                return False, "Cannot unblock yourself"

            success = await self.repository.unblock_user(db, blocker_id, blocked_id)
            if not success:
                return False, "User was not blocked"

            return True, "User unblocked successfully"

        except Exception as e:
            db.rollback()
            return False, f"Error unblocking user: {str(e)}"

    async def get_friends(
            self,
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 10
    ) -> List[FriendInfo]:
        try:
            # Get friends from repository (existing logic)
            friends = await self.repository.get_friends(db, user_id, skip, limit)
            
            # Extract friend IDs for batch query
            friend_ids = [friend.id for friend in friends]
            
            # Batch query for all default rooms at once
            default_rooms = db.query(
                Room.owner_id,
                Room.id
            ).filter(
                Room.owner_id.in_(friend_ids),
                Room.celebrant_id == func.cast(Room.owner_id, String),  # owner is celebrant
                Room.privacy_type == RoomPrivacy.PUBLIC,
                Room.is_archived == False
            ).all()
            
            # Create a mapping of user_id to default_room_id for O(1) lookup
            default_room_map = {
                room.owner_id: room.id for room in default_rooms
            }
            
            # Build response with default room IDs
            return [
                FriendInfo(
                    id=friend.id,
                    first_name=friend.first_name,
                    last_name=friend.last_name,
                    profile_picture_url=friend.profile_picture_url,
                    date_of_birth=friend.date_of_birth,
                    is_active=friend.is_active,
                    last_seen=friend.updated_at,
                    default_room_id=default_room_map.get(friend.id)  # Add this field
                ) for friend in friends
            ]
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error fetching friends: {str(e)}")