from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Any
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import settings
from app.api.deps import get_current_user
from app.core.database import get_db_dependency, create_tables
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.user_service import UserService
from app.core.security import create_jwt_token
from datetime import datetime,timedelta
class GoogleToken(BaseModel):
    token: str

class TokenResponse(BaseModel):
    status: str
    user_id: int
    email: str
    name: str = None
    profile_picture: str = None
    access_token: str = None

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    create_tables()


@app.post("/token", response_model=TokenResponse)
async def decode_token(
        token_data: GoogleToken,
        db: Session = Depends(get_db_dependency)
) -> Any:
    try:
        # Create credentials object
        credentials = Credentials(token_data.token)

        # Build the OAuth2 service
        service = build('oauth2', 'v2', credentials=credentials)

        # Get user info using the credentials
        user_info = service.userinfo().get().execute()

        # Extract user details
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')

        # Get or create user
        user = UserService.get_user_by_email(db, email)
        if not user:
            user = UserService.create_user(
                db,
                UserCreate(
                    email=email,
                    name=name,
                    profile_picture=picture
                )
            )

        # Create JWT token
        access_token = create_jwt_token(
            data={"sub": str(user.id)},  # sub is standard JWT claim for subject
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            "status": "success",
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "profile_picture": picture,
            "access_token": access_token  # Now sending our JWT token instead of Google token
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
@app.get("/users/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    return current_user

@app.put("/users/me", response_model=User)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
) -> Any:
    user = UserService.update_user(db, current_user, user_in)
    return user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)