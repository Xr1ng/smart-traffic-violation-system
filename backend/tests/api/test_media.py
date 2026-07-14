import pytest

from app.models.intake import Case, IntakeEvent, MediaAsset
from app.models.user import User
from app.core.security import create_access_token, hash_password


def _store_citizen_media(db, owner_id, filename):
    event = IntakeEvent(
        source_type="citizen",
        source_id=owner_id,
        image_hash=f"hash-{filename}",
    )
    db.add(event)
    db.flush()
    db.add(Case(case_no=f"CASE-{filename}", intake_event_id=event.id))
    db.add(MediaAsset(
        intake_event_id=event.id,
        asset_type="original",
        url=f"/media/{filename}",
        mime_type="image/jpeg",
        size=4,
    ))
    db.commit()


def test_get_media_returns_stored_file_for_owner(
    client, db, citizen_user, auth_headers, tmp_path, monkeypatch,
):
    image = b"\xff\xd8\xff\xd9"
    filename = "evidence.jpg"
    (tmp_path / filename).write_bytes(image)
    _store_citizen_media(db, citizen_user.id, filename)
    monkeypatch.setattr("app.core.config.settings.MEDIA_STORAGE_DIR", str(tmp_path))

    response = client.get(f"/api/v1/media/{filename}", headers=auth_headers)

    assert response.status_code == 200
    assert response.content == image
    assert response.headers["content-type"] == "image/jpeg"


def test_get_media_requires_authentication(client):
    response = client.get("/api/v1/media/evidence.jpg")

    assert response.status_code == 401


def test_get_media_denies_another_citizen(
    client, db, seeded_roles, citizen_user, tmp_path, monkeypatch,
):
    filename = "private.jpg"
    (tmp_path / filename).write_bytes(b"private")
    _store_citizen_media(db, citizen_user.id, filename)
    other = User(
        username="citizen-other",
        password_hash=hash_password("pass1234"),
        email="citizen-other@example.com",
        role_id=seeded_roles["citizen"].id,
    )
    db.add(other)
    db.commit()
    token = create_access_token(subject=str(other.id), role="citizen")
    monkeypatch.setattr("app.core.config.settings.MEDIA_STORAGE_DIR", str(tmp_path))

    response = client.get(
        f"/api/v1/media/{filename}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_get_media_allows_reviewer(
    client, db, citizen_user, reviewer_auth_headers, tmp_path, monkeypatch,
):
    filename = "review.jpg"
    image = b"review"
    (tmp_path / filename).write_bytes(image)
    _store_citizen_media(db, citizen_user.id, filename)
    monkeypatch.setattr("app.core.config.settings.MEDIA_STORAGE_DIR", str(tmp_path))

    response = client.get(
        f"/api/v1/media/{filename}", headers=reviewer_auth_headers,
    )

    assert response.status_code == 200
    assert response.content == image


def test_get_media_returns_404_for_missing_file(client, auth_headers, tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.MEDIA_STORAGE_DIR", str(tmp_path))

    response = client.get("/api/v1/media/missing.jpg", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.parametrize(
    "path_template",
    [
        pytest.param("/media/%2E%2E%5C{filename}", id="encoded-backslash"),
        pytest.param("/media/%2E%2E%2F{filename}", id="encoded-forward-slash"),
        pytest.param("/media/..\\{filename}", id="plain-backslash"),
        pytest.param("/media/../{filename}", id="dot-segment"),
    ],
)
def test_get_media_rejects_path_traversal(
    client, auth_headers, tmp_path, monkeypatch, path_template
):
    outside_file = tmp_path.parent / f"outside-{tmp_path.name}.jpg"
    outside_file.write_bytes(b"outside storage root")
    monkeypatch.setattr("app.core.config.settings.MEDIA_STORAGE_DIR", str(tmp_path))

    protected_path = path_template.format(filename=outside_file.name).replace(
        "/media/", "/api/v1/media/", 1
    )
    response = client.get(protected_path, headers=auth_headers)

    assert response.status_code == 404
