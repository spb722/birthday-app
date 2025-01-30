from sqlalchemy.orm import Session
from datetime import datetime, timedelta  # Fixed import here
from typing import Tuple, Optional
from feature.adapters.sms_adapter import SMSAdapter
from feature.repository.otp_repository import OTPRepository
from feature.utils.otp_generator import OTPUtils
from app.core.security import create_jwt_token
from app.core.config import settings
from app.models.user import User


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
        otp = "1234"  # For testing purposes
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
        # Commented out for testing
        # sms_sid = self.sms_adapter.send_sms(phone_number, message)
        sms_sid = 1223  # Mock SMS ID for testing

        if not sms_sid:
            return False, "Failed to send OTP", None

        return True, "OTP sent successfully", reference_id

    async def verify_otp(self, db: Session, phone_number: str, reference_id: str, otp_code: str) -> Tuple[
        bool, str, Optional[str]]:
        try:
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

            # Mark OTP as verified
            await OTPRepository.mark_as_verified(db, otp_record)

            # Find or create user with the verified phone number
            user = db.query(User).filter(User.phone == phone_number).first()

            if not user:
                # Create new user with updated field structure
                user = User(
                    phone=phone_number,
                    phone_verified="verified",
                    account_status="registered",
                    email=None,
                    first_name="",  # Using first_name instead of name
                    last_name="",  # Added last_name field
                    profile_picture_url="",
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                # Update existing user's fields
                user.phone_verified = "verified"
                user.account_status = "registered"
                if not user.first_name:
                    user.first_name = ""
                if not user.last_name:
                    user.last_name = ""
                if not user.profile_picture_url:
                    user.profile_picture_url = ""
                db.commit()
                db.refresh(user)

            # Generate JWT token with user ID
            access_token = create_jwt_token(
                data={"sub": str(user.id)},
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )

            return True, "OTP verified successfully", access_token

        except Exception as e:
            db.rollback()
            return False, f"Error during OTP verification: {str(e)}", None