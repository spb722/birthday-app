from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from feature.models.otp import OTP
from feature.utils.otp_generator import OTPUtils

class OTPRepository:
    @staticmethod
    async def create_otp(db: Session, phone_number: str, hashed_otp: str, reference_id: str, expiration_time: datetime) -> OTP:
        db_otp = OTP(
            phone_number=phone_number,
            hashed_otp=hashed_otp,
            reference_id=reference_id,
            expiration_time=expiration_time
        )
        db.add(db_otp)
        db.commit()
        db.refresh(db_otp)
        return db_otp

    @staticmethod
    async def get_otp_by_reference(db: Session, reference_id: str) -> Optional[OTP]:
        return db.query(OTP).filter(OTP.reference_id == reference_id).first()

    @staticmethod
    async def get_active_otp_by_phone(db: Session, phone_number: str) -> Optional[OTP]:
        return db.query(OTP).filter(
            OTP.phone_number == phone_number,
            OTP.expiration_time > datetime.utcnow(),
            OTP.is_verified == False
        ).first()

    @staticmethod
    async def increment_attempt_count(db: Session, otp: OTP) -> OTP:
        otp.attempt_count += 1
        db.commit()
        db.refresh(otp)
        return otp

    @staticmethod
    async def mark_as_verified(db: Session, otp: OTP) -> OTP:
        otp.is_verified = True
        db.commit()
        db.refresh(otp)
        return otp