# tests/api/test_violations_api.py


def test_list_violations_empty(client, reviewer_user, reviewer_auth_headers):
    r = client.get("/api/v1/violations", headers=reviewer_auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_owner_violations_empty(client, citizen_user, auth_headers):
    r = client.get(f"/api/v1/owners/{citizen_user.id}/violations", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_owner_violations_citizen_other_403(client, db, citizen_user, auth_headers, seeded_roles):
    from app.models.user import User
    other = User(username="citizen2", password_hash="h", email="citizen2@example.com",
                 role_id=seeded_roles["citizen"].id)
    db.add(other)
    db.flush()  # brief 漏写持久化：不 flush 则 other.id 为 None，other.id + 9999 会 TypeError
    # citizen_user 用自己的 token 查他人的 owner_id → 403
    r = client.get(f"/api/v1/owners/{other.id + 9999}/violations", headers=auth_headers)
    assert r.status_code == 403
