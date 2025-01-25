from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Any
# main.py
from feature.controllers.contact_controller import router as contact_router

# Add with other routers

from app.core.config import settings
from app.core.error_handler import (
    custom_http_exception_handler,
    validation_exception_handler,
    create_success_response,
    create_error_response
)
from app.schemas.response import SuccessResponse
from app.api.deps import get_current_user
from app.core.database import get_db_dependency, create_tables
from app.schemas.user import (
    User, UserCreate, UserUpdate, UserResponse,
    AuthResponse, PayloadData, AuthData
)
from app.services.user_service import UserService
from app.core.security import create_jwt_token
from feature.controllers.otp_controller import router as otp_router
from feature.controllers.friend_controller import router as friend_router

# Add this with your other app.include_router calls

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom exception handlers
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include routers
app.include_router(
    otp_router,
    prefix=settings.API_V1_STR,
    tags=["OTP"]
)

app.include_router(
    contact_router,
    prefix=settings.API_V1_STR,
    tags=["contacts"]
)
app.include_router(
    friend_router,
    prefix=settings.API_V1_STR,
    tags=["Friends"]
)

@app.on_event("startup")
async def startup_event():
    create_tables()


@app.post("/token", response_model=AuthResponse)
async def decode_token(
        token_data: dict,
        db: Session = Depends(get_db_dependency)
) -> Any:
    try:
        user_info = verify_google_token(token_data)  # Implement this function

        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')

        user = UserService.get_user_by_email(db, email)
        if not user:
            user = UserService.create_user(
                db,
                UserCreate(
                    email=email,
                    name=name,
                    profile_picture_url=picture
                )
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@app.get("/users/me", response_model=UserResponse)
async def read_users_me(
        current_user: User = Depends(get_current_user)
) -> Any:
    return create_success_response(
        message="User details retrieved successfully",
        data=current_user
    )


@app.put("/users/me", response_model=UserResponse)
async def update_user_me(
        user_in: UserUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db_dependency)
) -> Any:
    updated_user = UserService.update_user(db, current_user, user_in)
    return create_success_response(
        message="User updated successfully",
        data=updated_user
    )


@app.get("/health", response_model=SuccessResponse[dict])
async def health_check():
    return create_success_response(
        message="Service is healthy",
        data={
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "version": settings.VERSION
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)