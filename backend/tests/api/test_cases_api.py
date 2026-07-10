# tests/api/test_cases_api.py
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 10


def test_list_cases_reviewer(client, reviewer_user, pending_case, reviewer_auth_headers):
    r = client.get("/api/v1/cases", headers=reviewer_auth_headers)
    assert r.status_code == 200
    assert any(c["case_no"] == "CASE-PEND-1" for c in r.json()["items"])


def test_case_detail_reviewer(client, reviewer_user, pending_case, reviewer_auth_headers):
    r = client.get(f"/api/v1/cases/{pending_case.id}", headers=reviewer_auth_headers)
    assert r.status_code == 200
    assert r.json()["detection_result"] is None


def test_approve_endpoint(client, reviewer_user, citizen_user, pending_case, reviewer_auth_headers, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    from app.models.violation import NotificationTemplate, Vehicle
    # 直接在 db 注入 template + vehicle（通过 client 的 db override 不便，用 app 依赖的 db）
    # 这里用 reviewer 登录后调 approve；先确保 template/vehicle 存在
    r = client.post(f"/api/v1/cases/{pending_case.id}/approve", headers=reviewer_auth_headers,
                    json={"plate_no": "粤A12345", "violation_type": "超速", "fine_amount": 200,
                          "points": 6, "review_opinion": "清晰"})
    # 没车辆/模板时：violation 照建，notification=failed
    assert r.status_code == 200
    data = r.json()
    assert data["violation_no"].startswith("VIO")


def test_reject_endpoint(client, reviewer_user, pending_case, reviewer_auth_headers):
    r = client.post(f"/api/v1/cases/{pending_case.id}/reject", headers=reviewer_auth_headers,
                    json={"reject_reason": "模糊"})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_request_recheck_endpoint(client, reviewer_user, pending_case, reviewer_auth_headers):
    r = client.post(f"/api/v1/cases/{pending_case.id}/request-recheck", headers=reviewer_auth_headers)
    assert r.status_code == 202
    assert "Plan 2" in r.json()["message"]
