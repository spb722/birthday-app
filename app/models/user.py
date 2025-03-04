from sqlalchemy import Boolean, Column, String, Integer, DateTime
from sqlalchemy.sql import func
from ..core.database import Base
from sqlalchemy import Date
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(length=255))  # Replace name with first_name
    last_name = Column(String(length=255))  #
    email = Column(String(length=255), unique=True, index=True,nullable=True)  # Increased length
    phone = Column(String(length=20))
    profile_picture_url = Column(String(length=500))
    email_verified = Column(String(length=20), default='unverified')
    phone_verified = Column(String(length=20), default='unverified')
    account_status = Column(String(length=20), default='unregistered')
    hashed_password = Column(String(length=255), nullable=True)  # Increased length
    is_active = Column(Boolean, default=True)
    date_of_birth = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())