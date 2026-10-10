"""
Unit tests for the FastAPI app wiring (no DB / network)
"""

from collections import Counter

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from src.web.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestWebAPI:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["docs"] == "/docs"

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_correlation_id_echoed(self, client):
        response = client.get("/health", headers={"X-Correlation-ID": "abc-123"})
        assert response.headers["X-Correlation-ID"] == "abc-123"

    def test_no_route_registered_twice(self):
        keys = Counter(
            (route.path, method)
            for route in app.routes
            if isinstance(route, APIRoute)
            for method in route.methods
        )
        duplicates = [k for k, n in keys.items() if n > 1]
        assert duplicates == []

    def test_root_main_reuses_web_app(self):
        """Root main.py must not build a second app - it re-exports this one."""
        import importlib
        import sys
        from unittest.mock import patch

        sys.modules.pop("main", None)
        with patch.dict("os.environ", {"CONDA_DEFAULT_ENV": "torch_gpu"}):
            root_main = importlib.import_module("main")
        assert root_main.app is app


class TestWebAPIErrorHandling:
    def test_404_endpoint(self, client):
        assert client.get("/nonexistent").status_code == 404

    def test_method_not_allowed(self, client):
        assert client.put("/health").status_code == 405

    def test_nonexistent_api_route(self, client):
        assert client.get("/api/nonexistent").status_code == 404
