from datetime import datetime, timezone

from app.models.intake import Case, IntakeEvent
from app.models.violation import Violation


def _seed(db):
    t = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    ev = IntakeEvent(source_type="admin", image_hash="h" * 8)
    db.add(ev)
    db.flush()
    for no, st in [("C1", "approved"), ("C2", "rejected"), ("C3", "pending_human_review")]:
        db.add(Case(case_no=no, intake_event_id=ev.id, status=st, created_at=t))
    db.flush()
    c1 = db.query(Case).filter_by(case_no="C1").first()
    db.add(Violation(
        violation_no="V1", case_id=c1.id, plate_no="京A", violation_type="超速",
        location_text="路口A", fine_amount=200, points=3, status="pending", created_at=t,
    ))
    db.commit()


def test_overview_requires_auth(client):
    assert client.get("/api/v1/statistics/overview").status_code == 401


def test_overview_citizen_forbidden(client, citizen_user, auth_headers):
    assert client.get("/api/v1/statistics/overview", headers=auth_headers).status_code == 403


def test_overview_success(client, reviewer_user, reviewer_auth_headers, db):
    _seed(db)
    r = client.get("/api/v1/statistics/overview", headers=reviewer_auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_cases"] == 3
    assert data["approved_count"] == 1
    assert "period" in data


def test_by_location_success(client, reviewer_user, reviewer_auth_headers, db):
    _seed(db)
    r = client.get("/api/v1/statistics/by-location", headers=reviewer_auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json()["items"], list)


def test_by_type_success(client, reviewer_user, reviewer_auth_headers, db):
    _seed(db)
    r = client.get("/api/v1/statistics/by-type", headers=reviewer_auth_headers)
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1


def test_by_time_success(client, reviewer_user, reviewer_auth_headers, db):
    _seed(db)
    r = client.get("/api/v1/statistics/by-time", headers=reviewer_auth_headers)
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1


def test_by_location_requires_auth(client):
    assert client.get("/api/v1/statistics/by-location").status_code == 401


def test_by_location_citizen_forbidden(client, citizen_user, auth_headers):
    assert client.get("/api/v1/statistics/by-location", headers=auth_headers).status_code == 403


def test_by_type_requires_auth(client):
    assert client.get("/api/v1/statistics/by-type").status_code == 401


def test_by_type_citizen_forbidden(client, citizen_user, auth_headers):
    assert client.get("/api/v1/statistics/by-type", headers=auth_headers).status_code == 403


def test_by_time_requires_auth(client):
    assert client.get("/api/v1/statistics/by-time").status_code == 401


def test_by_time_citizen_forbidden(client, citizen_user, auth_headers):
    assert client.get("/api/v1/statistics/by-time", headers=auth_headers).status_code == 403


def test_overview_invalid_time_returns_422(client, reviewer_user, reviewer_auth_headers):
    r = client.get("/api/v1/statistics/overview?start_time=not-a-date", headers=reviewer_auth_headers)
    assert r.status_code == 422
