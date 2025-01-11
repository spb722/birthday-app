from typing import Generic, TypeVar, Optional, Any, Literal
from pydantic import BaseModel, Field

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    statusCode: int = Field(description="HTTP status code")
    status: str = Field(description="Response status (success/error)")
    message: str = Field(description="Response message")
    payload: Optional[T] = Field(default=None, description="Response payload data")

class ErrorResponse(BaseResponse[Any]):
    status: Literal["error"] = "error"
    payload: Optional[dict] = Field(
        default=None,
        description="Error details including error code and additional information"
    )

class SuccessResponse(BaseResponse[T]):
    status: Literal["success"] = "success"
    statusCode: Literal[200] = 200