# feature/models/room.py
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

class RoomPrivacy(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"

class RoomStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"

class Room(Base):
    __tablename__ = "rooms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_name = Column(String(255), nullable=False)
    privacy_type = Column(SQLEnum(RoomPrivacy), default=RoomPrivacy.PRIVATE)
    status = Column(SQLEnum(RoomStatus), default=RoomStatus.PENDING)
    activation_time = Column(DateTime(timezone=True), nullable=False)
    expiration_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Changed to unidirectional relationship
    owner = relationship("User", foreign_keys=[owner_id])
    participants = relationship("RoomParticipant", back_populates="room", cascade="all, delete-orphan")

class RoomParticipant(Base):
    __tablename__ = "room_participants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_admin = Column(Boolean, default=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected, banned
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    room = relationship("Room", back_populates="participants")
    user = relationship("User")