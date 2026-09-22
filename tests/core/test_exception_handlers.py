from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error_codes import ErrorCode
from app.core.exception_handlers import internal_server_error_handler
from app.core.messages import INTERNAL_SERVER_ERROR_MESSAGE


def test_internal_server_error_handler_returns_structured_error() -> None:
    # Arrange
    test_app = FastAPI()
    test_app.add_exception_handler(
        Exception,
        internal_server_error_handler,
    )

    @test_app.get("/error")
    async def error_route() -> None:
        raise RuntimeError("Test internal error")

    # Act
    with TestClient(
        test_app,
        raise_server_exceptions=False,
    ) as client:
        response = client.get("/error")

    # Assert
    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "code": ErrorCode.INTERNAL_SERVER_ERROR,
            "message": INTERNAL_SERVER_ERROR_MESSAGE,
        }
    }
