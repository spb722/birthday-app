from typing import Optional
from pydantic import BaseModel
from app.schemas.response import SuccessResponse

class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None

class TokenPayload(BaseModel):
    sub: Optional[int] = None

class TokenResponse(SuccessResponse[TokenData]):
    pass