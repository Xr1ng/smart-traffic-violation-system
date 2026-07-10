# tests/api/test_intakes.py
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 10


def test_citizen_upload_success(client, citizen_user, auth_headers, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    response = client.post(
        "/api/v1/intakes/citizen-reports",
        headers=auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口A"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_no"].startswith("CASE")
    assert data["status"] == "uploaded"


def test_citizen_upload_requires_auth(client):
    response = client.post(
        "/api/v1/intakes/citizen-reports",
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口A"},
    )
    assert response.status_code == 401


def test_citizen_upload_duplicate(client, citizen_user, auth_headers, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    client.post(
        "/api/v1/intakes/citizen-reports",
        headers=auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口A"},
    )
    response = client.post(
        "/api/v1/intakes/citizen-reports",
        headers=auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口A"},
    )
    assert response.status_code == 409


def test_citizen_report_persists_metadata(
    client, db, citizen_user, auth_headers, tmp_path, monkeypatch,
):
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    response = client.post(
        "/api/v1/intakes/citizen-reports",
        headers=auth_headers,
        files={"image": ("meta.jpg", JPEG, "image/jpeg")},
        data={
            "location_text": "测试路口",
            "captured_at": "2026-07-10T08:30:00",
            "description": "车辆闯红灯",
        },
    )

    assert response.status_code == 200
    from app.models.intake import Case

    event = db.get(Case, response.json()["case_id"]).intake_event
    assert getattr(event, "description", None) == "车辆闯红灯"
    assert event.captured_at is not None
    assert event.captured_at.isoformat().startswith("2026-07-10T08:30:00")


def test_admin_upload_persists_captured_at_and_speed(
    client, db, admin_user, admin_auth_headers, tmp_path, monkeypatch,
):
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    response = client.post(
        "/api/v1/intakes/admin-uploads",
        headers=admin_auth_headers,
        files={"image": ("admin.jpg", JPEG, "image/jpeg")},
        data={"location_text": "后台路口", "captured_at": "2026-07-10T09:15:00", "speed": "73.5"},
    )

    assert response.status_code == 200
    from app.models.intake import Case

    event = db.get(Case, response.json()["case_id"]).intake_event
    assert event.captured_at is not None
    assert event.captured_at.isoformat().startswith("2026-07-10T09:15:00")
    assert event.speed == 73.5


def test_camera_capture_success(client, camera_key, tmp_path, monkeypatch):
    raw_key, _ = camera_key
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    response = client.post(
        "/api/v1/intakes/camera-captures",
        headers={"X-Camera-Key": raw_key},
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口B", "speed": "88"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_no"].startswith("CASE")


def test_camera_capture_bad_key(client):
    response = client.post(
        "/api/v1/intakes/camera-captures",
        headers={"X-Camera-Key": "wrong"},
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口B"},
    )
    assert response.status_code == 401


def test_camera_capture_disabled_device(client, camera_device, camera_key, db, tmp_path, monkeypatch):
    raw_key, _ = camera_key
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    camera_device.status = "disabled"
    db.commit()
    response = client.post(
        "/api/v1/intakes/camera-captures",
        headers={"X-Camera-Key": raw_key},
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口B"},
    )
    assert response.status_code == 401
