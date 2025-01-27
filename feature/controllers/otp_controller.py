from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db_dependency
from feature.schemas.otp_schema import (
    OTPRequest,
    OTPVerify,
    OTPGenerateResponse,  # Changed from OTPResponse
    OTPVerifySuccessResponse,  # Changed from OTPVerifyResponse
    OTPResponseData,
    OTPVerifyResponseData
)
from app.core.error_handler import create_error_response, create_success_response
from feature.services.otp_service import OTPService

router = APIRouter(prefix="/otp", tags=["OTP"])
otp_service = OTPService()

@router.post("/generate", response_model=OTPGenerateResponse)
async def generate_otp(
    request: OTPRequest,
    db: Session = Depends(get_db_dependency)
):
    success, message, reference_id = await otp_service.generate_and_send_otp(
        db,
        request.phone_number
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    response_data = OTPResponseData(
        reference_id=reference_id,
        expires_in=300
    )

    return create_success_response(
        message="OTP sent successfully",
        data=response_data
    )

@router.post("/verify", response_model=OTPVerifySuccessResponse)
async def verify_otp(
    request: OTPVerify,
    db: Session = Depends(get_db_dependency)
):
    success, message, token = await otp_service.verify_otp(
        db,
        request.phone_number,
        request.reference_id,
        request.otp_code
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    response_data = OTPVerifyResponseData(
        access_token=token
    )

    return create_success_response(
        message="OTP verified successfully",
        data=response_data
    )