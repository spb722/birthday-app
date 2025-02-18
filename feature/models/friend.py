# feature/models/friend.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

class FriendRequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELED = "canceled"

class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(FriendRequestStatus), default=FriendRequestStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Add relationships
    requester = relationship(
        "User",
        foreign_keys=[requester_id],
        lazy="joined",
        innerjoin=True  # Ensures requester always exists
    )
    receiver = relationship(
        "User",
        foreign_keys=[receiver_id],
        lazy="joined",
        innerjoin=True  # Ensures receiver always exists
    )
    __table_args__ = (
        Index('idx_friend_request_users', 'requester_id', 'receiver_id'),
    )

class BlockedUser(Base):
    __tablename__ = "blocked_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    blocker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blocked_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Add relationships
    blocker = relationship("User", foreign_keys=[blocker_id], lazy="joined")
    blocked = relationship("User", foreign_keys=[blocked_id], lazy="joined")

    __table_args__ = (
        Index('idx_blocked_users', 'blocker_id', 'blocked_id', unique=True),
    )