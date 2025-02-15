# feature/repository/friend_repository.py
from sqlalchemy.orm import Session, joinedload
from ..models.friend import FriendRequest, BlockedUser, FriendRequestStatus
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from ..models.friend import FriendRequest, FriendRequestStatus
from app.models.user import User

class FriendRepository:
    @staticmethod
    async def get_friend_request(
            db: Session,
            request_id: str
    ) -> Optional[FriendRequest]:
        return db.query(FriendRequest) \
            .options(
            joinedload(FriendRequest.requester),
            joinedload(FriendRequest.receiver)
        ) \
            .filter(FriendRequest.id == request_id) \
            .first()

    @staticmethod
    async def get_existing_request(
            db: Session,
            requester_id: int,
            receiver_id: int
    ) -> Optional[FriendRequest]:
        return db.query(FriendRequest) \
            .options(
            joinedload(FriendRequest.requester),
            joinedload(FriendRequest.receiver)
        ) \
            .filter(
            and_(
                FriendRequest.requester_id == requester_id,
                FriendRequest.receiver_id == receiver_id,
                FriendRequest.status == FriendRequestStatus.PENDING
            )
        ).first()

    @staticmethod
    async def create_friend_request(
            db: Session,
            requester_id: int,
            receiver_id: int
    ) -> FriendRequest:
        friend_request = FriendRequest(
            requester_id=requester_id,
            receiver_id=receiver_id
        )
        db.add(friend_request)
        db.commit()
        db.refresh(friend_request)

        # Fetch with user details
        return db.query(FriendRequest) \
            .options(
            joinedload(FriendRequest.requester),
            joinedload(FriendRequest.receiver)
        ) \
            .filter(FriendRequest.id == friend_request.id) \
            .first()

    @staticmethod
    async def get_incoming_requests(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 10
    ) -> List[FriendRequest]:
        return db.query(FriendRequest) \
            .options(
            joinedload(FriendRequest.requester),
            joinedload(FriendRequest.receiver)
        ) \
            .filter(
            and_(
                FriendRequest.receiver_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING
            )
        ).offset(skip).limit(limit).all()

    @staticmethod
    async def get_outgoing_requests(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 10
    ) -> List[FriendRequest]:
        return db.query(FriendRequest) \
            .options(
            joinedload(FriendRequest.requester),
            joinedload(FriendRequest.receiver)
        ) \
            .filter(
            and_(
                FriendRequest.requester_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING
            )
        ).offset(skip).limit(limit).all()

    @staticmethod
    async def update_request_status(
            db: Session,
            request: FriendRequest,
            status: FriendRequestStatus
    ) -> FriendRequest:
        request.status = status
        db.add(request)
        db.commit()
        db.refresh(request)

        # Fetch with user details
        return db.query(FriendRequest) \
            .options(
            joinedload(FriendRequest.requester),
            joinedload(FriendRequest.receiver)
        ) \
            .filter(FriendRequest.id == request.id) \
            .first()

    @staticmethod
    async def is_blocked(
            db: Session,
            user_id: int,
            target_id: int
    ) -> bool:
        return db.query(BlockedUser).filter(
            or_(
                and_(BlockedUser.blocker_id == user_id,
                     BlockedUser.blocked_id == target_id),
                and_(BlockedUser.blocker_id == target_id,
                     BlockedUser.blocked_id == user_id)
            )
        ).first() is not None

    @staticmethod
    async def block_user(
            db: Session,
            blocker_id: int,
            blocked_id: int,
            reason: Optional[str] = None
    ) -> BlockedUser:
        blocked = BlockedUser(
            blocker_id=blocker_id,
            blocked_id=blocked_id,
            reason=reason
        )
        db.add(blocked)
        db.commit()
        db.refresh(blocked)
        return blocked

    @staticmethod
    async def unblock_user(
            db: Session,
            blocker_id: int,
            blocked_id: int
    ) -> bool:
        result = db.query(BlockedUser).filter(
            and_(
                BlockedUser.blocker_id == blocker_id,
                BlockedUser.blocked_id == blocked_id
            )
        ).delete()
        db.commit()
        return result > 0

    @staticmethod
    async def get_friends(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 10
    ) -> List[User]:
        # Get all accepted friend requests where the user is either the requester or receiver
        friend_requests = db.query(FriendRequest).filter(
            and_(
                or_(
                    FriendRequest.requester_id == user_id,
                    FriendRequest.receiver_id == user_id
                ),
                FriendRequest.status == FriendRequestStatus.ACCEPTED
            )
        ).all()

        # Extract friend IDs
        friend_ids = []
        for request in friend_requests:
            friend_id = request.receiver_id if request.requester_id == user_id else request.requester_id
            friend_ids.append(friend_id)

        # Get friend details
        return db.query(User).filter(
            User.id.in_(friend_ids)
        ).offset(skip).limit(limit).all()