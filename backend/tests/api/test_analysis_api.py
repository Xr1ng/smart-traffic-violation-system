from app.ai.adapters.base import LLMReportError, ReportNarrativeData


VALID_BODY = {
    "start_time": "2026-07-01T00:00:00Z",
    "end_time": "2026-07-31T23:59:59Z",
}


class FakeReportProvider:
    def generate_report(self, _payload):
        return ReportNarrativeData(
            summary="摘要",
            trend_analysis="趋势",
            hotspot_analysis="热点",
            risk_alerts=["风险"],
            recommendations=["建议"],
        )


class FailingReportProvider:
    def generate_report(self, _payload):
        raise LLMReportError("LLM 未配置")


def test_generate_report_success(
    client, reviewer_user, reviewer_auth_headers, monkeypatch,
):
    monkeypatch.setattr(
        "app.api.v1.analysis.get_llm_provider", lambda: FakeReportProvider(),
    )

    response = client.post(
        "/api/v1/analysis/reports",
        headers=reviewer_auth_headers,
        json=VALID_BODY,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "交通违章综合分析报告"
    assert data["summary"] == "摘要"
    assert data["risk_alerts"] == ["风险"]
    assert data["statistics_snapshot"]["overview"]["total_violations"] == 0
    assert data["author"] == "AI 分析助手"


def test_generate_report_requires_dates(
    client, reviewer_user, reviewer_auth_headers,
):
    response = client.post(
        "/api/v1/analysis/reports", headers=reviewer_auth_headers, json={},
    )
    assert response.status_code == 422


def test_generate_report_rejects_invalid_window(
    client, reviewer_user, reviewer_auth_headers,
):
    response = client.post(
        "/api/v1/analysis/reports",
        headers=reviewer_auth_headers,
        json={
            "start_time": "2026-07-02T00:00:00Z",
            "end_time": "2026-07-01T00:00:00Z",
        },
    )
    assert response.status_code == 422


def test_generate_report_maps_llm_error_to_503(
    client, reviewer_user, reviewer_auth_headers, monkeypatch,
):
    monkeypatch.setattr(
        "app.api.v1.analysis.get_llm_provider", lambda: FailingReportProvider(),
    )

    response = client.post(
        "/api/v1/analysis/reports",
        headers=reviewer_auth_headers,
        json=VALID_BODY,
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "LLM 报告服务暂不可用，请稍后重试"


def test_generate_report_requires_auth(client):
    assert client.post("/api/v1/analysis/reports", json=VALID_BODY).status_code == 401


def test_generate_report_citizen_forbidden(client, citizen_user, auth_headers):
    response = client.post(
        "/api/v1/analysis/reports", headers=auth_headers, json=VALID_BODY,
    )
    assert response.status_code == 403
