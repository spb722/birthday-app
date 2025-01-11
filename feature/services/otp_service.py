from sqlalchemy.orm import Session
from datetime import datetime
from typing import Tuple, Optional
from feature.adapters.sms_adapter import SMSAdapter
from feature.repository.otp_repository import OTPRepository
from feature.utils.otp_generator import OTPUtils
from app.core.security import create_jwt_token
from app.core.config import settings


class OTPService:
    def __init__(self):
        self.sms_adapter = SMSAdapter()
        self.max_attempts = 3
        self.otp_expiry_minutes = 5

    async def generate_and_send_otp(self, db: Session, phone_number: str) -> Tuple[bool, str, Optional[str]]:
        # Check if there's an active OTP
        existing_otp = await OTPRepository.get_active_otp_by_phone(db, phone_number)
        if existing_otp:
            return False, "An active OTP already exists", None

        # Generate new OTP
        otp = OTPUtils.generate_otp()
        reference_id = OTPUtils.generate_reference_id()
        hashed_otp = OTPUtils.hash_otp(otp)
        expiration_time = OTPUtils.get_otp_expiration_time(self.otp_expiry_minutes)

        # Create OTP record
        await OTPRepository.create_otp(
            db,
            phone_number,
            hashed_otp,
            reference_id,
            expiration_time
        )

        # Send OTP via SMS
        message = self.sms_adapter.format_otp_message(otp)
        sms_sid = self.sms_adapter.send_sms(phone_number, message)  # Removed await

        if not sms_sid:
            return False, "Failed to send OTP", None

        return True, "OTP sent successfully", reference_id

    async def verify_otp(self, db: Session, phone_number: str, reference_id: str, otp_code: str) -> Tuple[
        bool, str, Optional[str]]:
        # Get OTP record
        otp_record = await OTPRepository.get_otp_by_reference(db, reference_id)

        if not otp_record:
            return False, "Invalid reference ID", None

        if otp_record.phone_number != phone_number:
            return False, "Phone number doesn't match", None

        if otp_record.is_verified:
            return False, "OTP already verified", None

        if otp_record.expiration_time < datetime.utcnow():
            return False, "OTP has expired", None

        if otp_record.attempt_count >= self.max_attempts:
            return False, "Maximum verification attempts exceeded", None

        # Increment attempt count
        await OTPRepository.increment_attempt_count(db, otp_record)

        # Verify OTP
        if not OTPUtils.verify_otp(otp_code, otp_record.hashed_otp):
            return False, "Invalid OTP", None

        # Mark as verified
        await OTPRepository.mark_as_verified(db, otp_record)

        # Generate JWT token
        access_token = create_jwt_token(
            data={"sub": phone_number}
        )

        return True, "OTP verified successfully", access_token