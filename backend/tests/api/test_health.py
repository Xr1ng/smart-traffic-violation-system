def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_excludes_removed_rule_configuration_routes(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert not any(path.startswith("/api/v1/admin/rules") for path in paths)
    assert "/internal/ai/rules/evaluate" in paths
