from fastapi.testclient import TestClient


def test_health_check_returns_ok(
    client: TestClient,
) -> None:
    # Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }