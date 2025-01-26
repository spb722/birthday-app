from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
from pydantic import BaseModel, Field
from app.core.database import get_db_dependency
from app.schemas.token import TokenResponse
from app.core.security import create_jwt_token
from datetime import timedelta
from app.core.config import settings
from app.schemas.user import AuthResponse, AuthData, PayloadData
from app.services.user_service import UserService
from app.core.error_handler import create_success_response
router = APIRouter()

class PhoneLoginRequest(BaseModel):
    phone: str = Field(..., pattern=r'^\+?1?\d{9,15}$')
    password: str

@router.post("/phone-login", response_model=AuthResponse)
async def phone_login(
    request: PhoneLoginRequest,
    db: Session = Depends(get_db_dependency)
) -> Any:
    user = UserService.authenticate_phone(db, request.phone, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password"
        )

    access_token = create_jwt_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    auth_data = AuthData(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    payload_data = PayloadData(
        user=user,
        auth=auth_data
    )

    return create_success_response(
        message="Authentication successful",
        data=payload_data
    )