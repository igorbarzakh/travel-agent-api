from app.core.error_codes import ErrorCode
from app.core.messages import (
    INVALID_CREDENTIALS_ERROR_MESSAGE,
    INVALID_REFRESH_TOKEN_ERROR_MESSAGE,
    USER_ALREADY_EXISTS_ERROR_MESSAGE,
)
from app.schemas.error import ErrorResponse


RECOMMENDATION_RESPONSES = {
    502: {
        "model": ErrorResponse,
        "description": "Failed to get a response from the LLM",
    },
}


STREAM_RECOMMENDATION_RESPONSES = {
    200: {
        "description": "SSE stream with recommendation events",
        "content": {
            "text/event-stream": {
                "schema": {
                    "type": "string",
                },
            },
        },
    },
    **RECOMMENDATION_RESPONSES,
}


REGISTER_RESPONSES = {
    409: {
        "model": ErrorResponse,
        "description": USER_ALREADY_EXISTS_ERROR_MESSAGE,
        "content": {
            "application/json": {
                "example": {
                    "detail": {
                        "code": ErrorCode.USER_ALREADY_EXISTS,
                        "message": USER_ALREADY_EXISTS_ERROR_MESSAGE,
                    }
                }
            }
        },
    },
}

LOGIN_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": INVALID_CREDENTIALS_ERROR_MESSAGE,
        "content": {
            "application/json": {
                "example": {
                    "detail": {
                        "code": ErrorCode.INVALID_CREDENTIALS,
                        "message": INVALID_CREDENTIALS_ERROR_MESSAGE,
                    }
                }
            }
        },
    },
}

REFRESH_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": INVALID_REFRESH_TOKEN_ERROR_MESSAGE,
        "content": {
            "application/json": {
                "example": {
                    "detail": {
                        "code": ErrorCode.INVALID_REFRESH_TOKEN,
                        "message": INVALID_REFRESH_TOKEN_ERROR_MESSAGE,
                    }
                }
            }
        },
    },
}

LOGOUT_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": INVALID_REFRESH_TOKEN_ERROR_MESSAGE,
        "content": {
            "application/json": {
                "example": {
                    "detail": {
                        "code": ErrorCode.INVALID_REFRESH_TOKEN,
                        "message": INVALID_REFRESH_TOKEN_ERROR_MESSAGE,
                    }
                }
            }
        },
    },
}
