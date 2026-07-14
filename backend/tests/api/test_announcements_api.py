from datetime import datetime, timezone

import pytest

from app.models.announcement import Announcement
from app.models.violation import AuditLog
from app.services.announcement_service import AnnouncementService


def test_authenticated_roles_can_list_and_read_announcements(
    client,
    db,
    admin_user,
    auth_headers,
    reviewer_auth_headers,
    admin_auth_headers,
):
    announcement = AnnouncementService(db).create(
        title="系统维护", content="今晚维护", actor_id=admin_user.id
    )

    for headers in (auth_headers, reviewer_auth_headers, admin_auth_headers):
        listed = client.get("/api/v1/announcements", headers=headers)
        detail = client.get(
            f"/api/v1/announcements/{announcement.id}", headers=headers
        )

        assert listed.status_code == 200
        assert listed.json() == {
            "items": [detail.json()],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
        assert detail.status_code == 200
        assert detail.json()["title"] == "系统维护"
        assert detail.json()["content"] == "今晚维护"


@pytest.mark.parametrize(
    "path", ["/api/v1/announcements", "/api/v1/announcements/1"]
)
def test_announcement_reads_require_authentication(client, path):
    assert client.get(path).status_code == 401


def test_missing_announcement_read_returns_404(client, auth_headers):
    response = client.get("/api/v1/announcements/9999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "公告不存在"}


@pytest.mark.parametrize("method", ["post", "patch", "delete"])
def test_announcement_writes_require_authentication(client, method):
    if method == "post":
        response = client.post(
            "/api/v1/admin/announcements",
            json={"title": "未登录", "content": "禁止"},
        )
    elif method == "patch":
        response = client.patch(
            "/api/v1/admin/announcements/1", json={"title": "未登录"}
        )
    else:
        response = client.delete("/api/v1/admin/announcements/1")

    assert response.status_code == 401


@pytest.mark.parametrize("headers_fixture", ["auth_headers", "reviewer_auth_headers"])
@pytest.mark.parametrize("method", ["post", "patch", "delete"])
def test_announcement_writes_require_admin_role(
    client, db, admin_user, request, headers_fixture, method
):
    announcement = AnnouncementService(db).create(
        title="原公告", content="原正文", actor_id=admin_user.id
    )
    headers = request.getfixturevalue(headers_fixture)
    if method == "post":
        response = client.post(
            "/api/v1/admin/announcements",
            headers=headers,
            json={"title": "越权", "content": "禁止"},
        )
    elif method == "patch":
        response = client.patch(
            f"/api/v1/admin/announcements/{announcement.id}",
            headers=headers,
            json={"title": "越权"},
        )
    else:
        response = client.delete(
            f"/api/v1/admin/announcements/{announcement.id}", headers=headers
        )

    assert response.status_code == 403


def test_admin_crud_preserves_omitted_content_and_writes_exact_audit_actions(
    client, db, admin_user, admin_auth_headers
):
    created = client.post(
        "/api/v1/admin/announcements",
        headers=admin_auth_headers,
        json={"title": "  系统维护  ", "content": "  今晚维护  "},
    )

    assert created.status_code == 201
    announcement_id = created.json()["id"]
    assert created.json()["title"] == "系统维护"
    assert created.json()["content"] == "今晚维护"
    assert created.json()["created_by"] == admin_user.id

    updated = client.patch(
        f"/api/v1/admin/announcements/{announcement_id}",
        headers=admin_auth_headers,
        json={"title": "  维护时间调整  "},
    )

    assert updated.status_code == 200
    assert updated.json()["title"] == "维护时间调整"
    assert updated.json()["content"] == "今晚维护"

    deleted = client.delete(
        f"/api/v1/admin/announcements/{announcement_id}",
        headers=admin_auth_headers,
    )

    assert deleted.status_code == 204
    assert deleted.content == b""
    logs = (
        db.query(AuditLog)
        .filter_by(target_type="announcement", target_id=announcement_id)
        .order_by(AuditLog.id)
        .all()
    )
    assert [log.action for log in logs] == [
        "announcement_create",
        "announcement_update",
        "announcement_delete",
    ]
    assert [log.actor_id for log in logs] == [admin_user.id] * 3


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "   ", "content": "正文"},
        {"title": "标题", "content": "   "},
        {"title": "题" * 101, "content": "正文"},
        {"title": "标题", "content": "文" * 5001},
    ],
)
def test_create_rejects_blank_and_oversized_inputs(
    client, admin_auth_headers, payload
):
    response = client.post(
        "/api/v1/admin/announcements", headers=admin_auth_headers, json=payload
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": "   "},
        {"content": "   "},
        {"title": "题" * 101},
        {"content": "文" * 5001},
    ],
)
def test_update_rejects_empty_blank_and_oversized_inputs(
    client, db, admin_user, admin_auth_headers, payload
):
    announcement = AnnouncementService(db).create(
        title="原公告", content="原正文", actor_id=admin_user.id
    )

    response = client.patch(
        f"/api/v1/admin/announcements/{announcement.id}",
        headers=admin_auth_headers,
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_missing_announcement_write_returns_404(
    client, admin_auth_headers, method
):
    path = "/api/v1/admin/announcements/9999"
    if method == "patch":
        response = client.patch(
            path, headers=admin_auth_headers, json={"title": "不存在"}
        )
    else:
        response = client.delete(path, headers=admin_auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "公告不存在"}


def test_announcement_list_pagination_has_stable_updated_at_and_id_order(
    client, db, admin_user, auth_headers
):
    service = AnnouncementService(db)
    first = service.create(title="第一条", content="正文", actor_id=admin_user.id)
    second = service.create(title="第二条", content="正文", actor_id=admin_user.id)
    third = service.create(title="第三条", content="正文", actor_id=admin_user.id)
    first.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    second.updated_at = datetime(2026, 1, 2, tzinfo=timezone.utc)
    third.updated_at = datetime(2026, 1, 2, tzinfo=timezone.utc)
    db.commit()

    first_page = client.get(
        "/api/v1/announcements?page=1&page_size=2", headers=auth_headers
    )
    second_page = client.get(
        "/api/v1/announcements?page=2&page_size=2", headers=auth_headers
    )

    assert first_page.status_code == 200
    assert [item["id"] for item in first_page.json()["items"]] == [
        third.id,
        second.id,
    ]
    assert first_page.json()["total"] == 3
    assert first_page.json()["page"] == 1
    assert first_page.json()["page_size"] == 2
    assert [item["id"] for item in second_page.json()["items"]] == [first.id]
    assert second_page.json()["total"] == 3
    assert second_page.json()["page"] == 2
    assert second_page.json()["page_size"] == 2
