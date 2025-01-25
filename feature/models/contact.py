# feature/models/contact.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class ContactRegistry(Base):
    __tablename__ = "contact_registry"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    contact_name = Column(String(255))
    registered_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_contact_phone_owner', 'phone_number', 'owner_id'),
    )