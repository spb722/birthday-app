from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from typing import Union, Any


async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "statusCode": exc.status_code,
            "status": "error",
            "message": str(exc.detail),
            "payload": None
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join([str(x) for x in error["loc"]]),
            "message": error["msg"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "statusCode": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "status": "error",
            "message": "Validation error",
            "payload": {
                "errors": error_details
            }
        }
    )


def create_error_response(status_code: int, message: str, error_details: Union[dict, None] = None) -> dict:
    return {
        "statusCode": status_code,
        "status": "error",
        "message": message,
        "payload": error_details
    }


def create_success_response(message: str, data: Any = None) -> dict:
    return {
        "statusCode": 200,
        "status": "success",
        "message": message,
        "payload": data
    }