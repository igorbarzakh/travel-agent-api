from pydantic import BaseModel

from app.core.error_codes import ErrorCode


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail
