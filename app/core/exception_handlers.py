import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.error_codes import ErrorCode
from app.core.messages import INTERNAL_SERVER_ERROR_MESSAGE
from app.schemas.error import ErrorDetail, ErrorResponse


logger = logging.getLogger(__name__)


async def internal_server_error_handler(
    request: Request,
    error: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled exception during request %s %s",
        request.method,
        request.url.path,
        exc_info=error,
    )

    response = ErrorResponse(
        detail=ErrorDetail(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=INTERNAL_SERVER_ERROR_MESSAGE,
        )
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(),
    )
