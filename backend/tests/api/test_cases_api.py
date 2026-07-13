# tests/api/test_cases_api.py
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 10


def test_list_cases_reviewer(client, reviewer_user, pending_case, reviewer_auth_headers):
    pending_case.violation_type = "illegal_stop"
    r = client.get("/api/v1/cases", headers=reviewer_auth_headers)
    assert r.status_code == 200
    item = next(c for c in r.json()["items"] if c["case_no"] == "CASE-PEND-1")
    assert item["violation_type"] == "违停"


def test_list_cases_includes_source_description_media_and_reward(
    client, db, citizen_user, reviewer_user, pending_case, reviewer_auth_headers,
):
    from app.models.intake import MediaAsset
    from app.models.violation import Reward

    event = pending_case.intake_event
    event.description = "车辆闯红灯"
    db.add(MediaAsset(
        intake_event_id=event.id,
        asset_type="original",
        url="/media/original/evidence.jpg",
        mime_type="image/jpeg",
        size=14,
    ))
    db.add(Reward(citizen_id=citizen_user.id, case_id=pending_case.id, amount=20))
    db.commit()

    response = client.get("/api/v1/cases", headers=reviewer_auth_headers)

    assert response.status_code == 200
    item = next(item for item in response.json()["items"] if item["id"] == pending_case.id)
    assert item.get("source_desc") == "市民举报"
    assert item.get("description") == "车辆闯红灯"
    assert item.get("media") == {"original_url": "/media/original/evidence.jpg"}
    assert item.get("reward") == 20


def test_list_cases_keyword_matches_case_number_plate_and_location(
    client, db, reviewer_user, pending_case, reviewer_auth_headers,
):
    from app.models.intake import Case, IntakeEvent

    pending_case.plate_no = "粤AKEY01"
    other_event = IntakeEvent(
        source_type="camera",
        source_id=None,
        image_hash="keyword-distractor",
        location_text="无关地点",
    )
    db.add(other_event)
    db.flush()
    db.add(Case(
        case_no="CASE-OTHER-2",
        intake_event_id=other_event.id,
        status="pending_human_review",
        plate_no="粤BOTHER",
    ))
    db.commit()

    for keyword in ("PEND-1", "粤AKEY", "路口A"):
        response = client.get(
            "/api/v1/cases",
            headers=reviewer_auth_headers,
            params={"keyword": keyword},
        )
        assert response.status_code == 200
        assert [item["case_no"] for item in response.json()["items"]] == ["CASE-PEND-1"]


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
