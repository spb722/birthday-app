from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean,
    ForeignKey, Enum as SQLEnum, JSON, Index, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum
from datetime import datetime

class RoomPrivacy(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class RoomStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class RoomType(str, enum.Enum):
    EVENT = "event"
    GROUP = "group"
    MEETING = "meeting"


class Room(Base):
    __tablename__ = "rooms"

    # Primary Key and Relations
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    celebrant_id = Column(String(36), index=True)
    celebrant_birthday = Column(Date, nullable=True)
    # Basic Information
    room_name = Column(String(255), nullable=False)
    description = Column(String(1000))
    room_type = Column(SQLEnum(RoomType), default=RoomType.EVENT)
    privacy_type = Column(SQLEnum(RoomPrivacy), default=RoomPrivacy.PRIVATE)

    # Room Settings
    max_participants = Column(Integer, default=100)
    auto_approve_participants = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)

    # Status and Timing
    status = Column(SQLEnum(RoomStatus), default=RoomStatus.PENDING)
    activation_time = Column(DateTime(timezone=True), nullable=False)
    expiration_time = Column(DateTime(timezone=True), nullable=False)

    # Tracking and Metadata
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    room_metadata = Column(JSON, default=dict)  # Changed from metadata to room_metadata

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    participants = relationship("RoomParticipant", back_populates="room", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_room_status_timing', 'status', 'activation_time', 'expiration_time'),
        Index('idx_room_type_privacy', 'room_type', 'privacy_type'),
    )

    def is_active(self) -> bool:
        """Check if the room is currently active."""
        current_time = datetime.utcnow()
        return (
                self.status == RoomStatus.ACTIVE and
                self.activation_time <= current_time and
                self.expiration_time > current_time and
                not self.is_archived
        )

    def can_join(self) -> bool:
        """Check if new participants can join the room."""
        return (
                self.is_active() and
                (self.max_participants is None or
                 len(self.participants) < self.max_participants)
        )


class RoomParticipant(Base):
    __tablename__ = "room_participants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String(36), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Participant Status and Role
    is_admin = Column(Boolean, default=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected, banned

    # Tracking
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True))

    # Relationships
    room = relationship("Room", back_populates="participants")
    user = relationship("User")

    # Indexes for performance
    __table_args__ = (
        Index('idx_room_participant', 'room_id', 'user_id', unique=True),
        Index('idx_participant_status', 'status'),
    )