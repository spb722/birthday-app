from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class OTP(Base):
    __tablename__ = "otps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(20), nullable=False, index=True)
    hashed_otp = Column(String(255), nullable=False)
    reference_id = Column(String(36), unique=True, nullable=False)
    expiration_time = Column(DateTime(timezone=True), nullable=False)
    attempt_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())