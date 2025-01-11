import random
import string
from datetime import datetime, timedelta
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class OTPUtils:
    @staticmethod
    def generate_otp(length: int = 4) -> str:
        """Generate a random OTP of specified length"""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def generate_reference_id() -> str:
        """Generate a unique reference ID"""
        return str(uuid.uuid4())

    @staticmethod
    def hash_otp(otp: str) -> str:
        """Hash the OTP using bcrypt"""
        return pwd_context.hash(otp)

    @staticmethod
    def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
        """Verify if the plain OTP matches the hashed OTP"""
        return pwd_context.verify(plain_otp, hashed_otp)

    @staticmethod
    def get_otp_expiration_time(minutes: int = 5) -> datetime:
        """Get OTP expiration time"""
        return datetime.utcnow() + timedelta(minutes=minutes)