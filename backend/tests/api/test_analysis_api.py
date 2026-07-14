from app.ai.adapters.base import LLMReportError, ReportNarrativeData
from app.services.report_storage import ReportStorageError


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
    client, reviewer_user, reviewer_auth_headers, monkeypatch, tmp_path,
):
    monkeypatch.setattr(
        "app.api.v1.analysis.get_llm_provider", lambda: FakeReportProvider(),
    )
    monkeypatch.setattr("app.api.v1.analysis.settings.REPORT_STORAGE_DIR", str(tmp_path))

    response = client.post(
        "/api/v1/analysis/reports",
        headers=reviewer_auth_headers,
        json=VALID_BODY,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["id"]) == 12
    assert data["title"] == "交通违章综合分析报告"
    assert data["summary"] == "摘要"
    assert data["risk_alerts"] == ["风险"]
    assert data["statistics_snapshot"]["overview"]["total_violations"] == 0
    assert data["author"] == "AI 分析助手"
    assert len(list(tmp_path.glob("*.md"))) == 1


def test_history_list_and_detail_return_saved_report(
    client, reviewer_user, reviewer_auth_headers, monkeypatch, tmp_path,
):
    monkeypatch.setattr(
        "app.api.v1.analysis.get_llm_provider", lambda: FakeReportProvider(),
    )
    monkeypatch.setattr("app.api.v1.analysis.settings.REPORT_STORAGE_DIR", str(tmp_path))
    created = client.post(
        "/api/v1/analysis/reports",
        headers=reviewer_auth_headers,
        json=VALID_BODY,
    ).json()

    history = client.get(
        "/api/v1/analysis/reports",
        headers=reviewer_auth_headers,
        params={
            "page": 1,
            "page_size": 20,
            "start_time": "2026-07-15T00:00:00Z",
            "end_time": "2026-07-15T23:59:59Z",
        },
    )
    detail = client.get(
        f"/api/v1/analysis/reports/{created['id']}",
        headers=reviewer_auth_headers,
    )

    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["id"] == created["id"]
    assert detail.status_code == 200
    assert detail.json() == created


def test_history_list_requires_a_complete_valid_date_range(
    client, reviewer_user, reviewer_auth_headers, monkeypatch, tmp_path,
):
    monkeypatch.setattr("app.api.v1.analysis.settings.REPORT_STORAGE_DIR", str(tmp_path))

    missing_end = client.get(
        "/api/v1/analysis/reports",
        headers=reviewer_auth_headers,
        params={"start_time": "2026-07-01T00:00:00Z"},
    )
    reversed_range = client.get(
        "/api/v1/analysis/reports",
        headers=reviewer_auth_headers,
        params={
            "start_time": "2026-07-02T00:00:00Z",
            "end_time": "2026-07-01T00:00:00Z",
        },
    )

    assert missing_end.status_code == 422
    assert reversed_range.status_code == 422


def test_history_detail_maps_missing_and_corrupt_files(
    client, reviewer_user, reviewer_auth_headers, monkeypatch, tmp_path,
):
    monkeypatch.setattr("app.api.v1.analysis.settings.REPORT_STORAGE_DIR", str(tmp_path))

    missing = client.get(
        "/api/v1/analysis/reports/0123456789ab",
        headers=reviewer_auth_headers,
    )
    (tmp_path / "2026-07-01_2026-07-31_20260714T000000Z_abcdef123456.md").write_text(
        "broken", encoding="utf-8",
    )
    corrupt = client.get(
        "/api/v1/analysis/reports/abcdef123456",
        headers=reviewer_auth_headers,
    )

    assert missing.status_code == 404
    assert corrupt.status_code == 500
    assert corrupt.json()["detail"] == "历史报告文件损坏，无法读取"


def test_generate_report_maps_storage_error_to_500(
    client, reviewer_user, reviewer_auth_headers, monkeypatch,
):
    monkeypatch.setattr(
        "app.api.v1.analysis.get_llm_provider", lambda: FakeReportProvider(),
    )

    def fail_save(_self, _report):
        raise ReportStorageError("历史报告保存失败")

    monkeypatch.setattr("app.api.v1.analysis.ReportStorageService.save", fail_save)

    response = client.post(
        "/api/v1/analysis/reports",
        headers=reviewer_auth_headers,
        json=VALID_BODY,
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "报告已生成但保存失败，请稍后重试"


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
    client, reviewer_user, reviewer_auth_headers, monkeypatch, tmp_path,
):
    monkeypatch.setattr(
        "app.api.v1.analysis.get_llm_provider", lambda: FailingReportProvider(),
    )
    monkeypatch.setattr("app.api.v1.analysis.settings.REPORT_STORAGE_DIR", str(tmp_path))

    response = client.post(
        "/api/v1/analysis/reports",
        headers=reviewer_auth_headers,
        json=VALID_BODY,
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "LLM 报告服务暂不可用，请稍后重试"
    assert list(tmp_path.glob("*.md")) == []


def test_generate_report_requires_auth(client):
    assert client.post("/api/v1/analysis/reports", json=VALID_BODY).status_code == 401
    assert client.get("/api/v1/analysis/reports").status_code == 401
    assert client.get("/api/v1/analysis/reports/0123456789ab").status_code == 401


def test_generate_report_citizen_forbidden(client, citizen_user, auth_headers):
    response = client.post(
        "/api/v1/analysis/reports", headers=auth_headers, json=VALID_BODY,
    )
    assert response.status_code == 403

    assert client.get(
        "/api/v1/analysis/reports", headers=auth_headers,
    ).status_code == 403
    assert client.get(
        "/api/v1/analysis/reports/0123456789ab", headers=auth_headers,
    ).status_code == 403
