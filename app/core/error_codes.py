from enum import StrEnum


class ErrorCode(StrEnum):
    LLM_REQUEST_FAILED = "LLM_REQUEST_FAILED"
    EMPTY_LLM_RESPONSE = "EMPTY_LLM_RESPONSE"
