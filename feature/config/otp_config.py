from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field


class OTPSettings(BaseSettings):
    # OTP Generation Settings
    OTP_LENGTH: int = Field(default=4, description="Length of the OTP")
    OTP_EXPIRY_MINUTES: int = Field(default=5, description="OTP validity period in minutes")
    OTP_MAX_ATTEMPTS: int = Field(default=3, description="Maximum verification attempts allowed")

    # Rate Limiting Settings
    OTP_RATE_LIMIT_MINUTES: int = Field(default=15, description="Rate limit window in minutes")
    OTP_MAX_REQUESTS: int = Field(default=3, description="Maximum OTP requests allowed in rate limit window")

    # Twilio Settings
    TWILIO_ACCOUNT_SID: str = Field(default="", description="Twilio Account SID")
    TWILIO_AUTH_TOKEN: str = Field(default="", description="Twilio Auth Token")
    TWILIO_FROM_NUMBER: str = Field(default="", description="Twilio Phone Number")

    # Message Templates
    OTP_MESSAGE_TEMPLATE: str = Field(
        default="Your verification code is: {otp}. Valid for {expiry} minutes.",
        description="Template for OTP SMS message"
    )

    # Error Messages
    ERROR_MESSAGES = {
        "rate_limit": "Too many OTP requests. Please try again after {minutes} minutes.",
        "invalid_phone": "Invalid phone number format.",
        "invalid_otp": "Invalid OTP provided.",
        "expired_otp": "OTP has expired. Please request a new one.",
        "max_attempts": "Maximum verification attempts exceeded. Please request a new OTP.",
        "already_verified": "This OTP has already been verified.",
        "sms_failed": "Failed to send OTP via SMS. Please try again.",
        "active_otp": "An active OTP already exists for this number. Please wait for it to expire."
    }

    class Config:
        case_sensitive = True
        env_file = ".env"


otp_settings = OTPSettings()