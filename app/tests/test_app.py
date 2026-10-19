import os
import tempfile

os.environ["APP_LOG_DIR"] = tempfile.mkdtemp(prefix="server-devops-test-logs-")

from app.app import app  # noqa: E402


def test_home_returns_greeting():
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Hello, World!"


def test_health_returns_healthy_status():
    response = app.test_client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}


def test_demo_error_returns_server_error():
    response = app.test_client().get("/demo-error")

    assert response.status_code == 500
    assert response.get_json()["status"] == "error"


def test_metrics_exposes_request_counters_and_excludes_scrapes():
    client = app.test_client()
    client.get("/health")
    response = client.get("/metrics")
    metrics = response.get_data(as_text=True)

    assert response.status_code == 200
    health_counter = next(
        line
        for line in metrics.splitlines()
        if line.startswith("http_requests_total{") and 'endpoint="/health"' in line
    )
    assert 'method="GET"' in health_counter
    assert 'status_code="200"' in health_counter
    assert 'endpoint="/metrics"' not in metrics
