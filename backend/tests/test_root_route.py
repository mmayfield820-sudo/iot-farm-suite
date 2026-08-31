"""验证根路由返回项目信息。"""

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_root_route_returns_project_metadata() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Smart Farm API"
    assert response.json()["docs"] == "/docs"
