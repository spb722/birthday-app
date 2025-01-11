from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.schemas.response import BaseResponse, SuccessResponse

class OTPRequest(BaseModel):
    phone_number: str = Field(..., pattern=r'^\+?1?\d{9,15}$')

class OTPVerify(BaseModel):
    phone_number: str = Field(..., pattern=r'^\+?1?\d{9,15}$')
    reference_id: str
    otp_code: str = Field(..., min_length=4, max_length=4)

class OTPResponseData(BaseModel):
    reference_id: str
    expires_in: int  # seconds

class OTPVerifyResponseData(BaseModel):
    access_token: Optional[str] = None

class OTPGenerateResponse(SuccessResponse[OTPResponseData]):
    pass

class OTPVerifySuccessResponse(SuccessResponse[OTPVerifyResponseData]):
    pass