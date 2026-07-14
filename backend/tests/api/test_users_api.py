def test_create_user_requires_auth(client):
    assert client.post("/api/v1/admin/users", json={
        "username": "x", "password": "p", "role_code": "citizen"}).status_code == 401


def test_create_user_reviewer_forbidden(client, reviewer_user, reviewer_auth_headers):
    r = client.post("/api/v1/admin/users", headers=reviewer_auth_headers,
                    json={"username": "x", "password": "p", "email": "x@example.com", "role_code": "citizen"})
    assert r.status_code == 403


def test_create_user_success(client, admin_user, admin_auth_headers):
    r = client.post("/api/v1/admin/users", headers=admin_auth_headers, json={
        "username": "newrev", "password": "pass1234", "phone": "138",
        "email": "r@e.com", "role_code": "reviewer"})
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "newrev"
    assert data["role_code"] == "reviewer"
    assert data["status"] == "active"


def test_list_users(client, admin_user, admin_auth_headers):
    client.post("/api/v1/admin/users", headers=admin_auth_headers,
                json={"username": "a", "password": "p", "email": "a@example.com", "role_code": "citizen"})
    r = client.get("/api/v1/admin/users", headers=admin_auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_get_user_404(client, admin_user, admin_auth_headers):
    assert client.get("/api/v1/admin/users/9999", headers=admin_auth_headers).status_code == 404


def test_patch_user(client, admin_user, admin_auth_headers):
    uid = client.post("/api/v1/admin/users", headers=admin_auth_headers,
                      json={"username": "a", "password": "p", "email": "a@example.com", "role_code": "citizen"}).json()["id"]
    r = client.patch(f"/api/v1/admin/users/{uid}", headers=admin_auth_headers,
                     json={"status": "disabled", "phone": "139"})
    assert r.status_code == 200
    assert r.json()["status"] == "disabled"
    assert r.json()["phone"] == "139"


def test_created_user_can_login(client, admin_user, admin_auth_headers):
    """端到端：admin 建的用户能用 /auth/login 登录。"""
    client.post("/api/v1/admin/users", headers=admin_auth_headers, json={
        "username": "loginme", "password": "pass1234", "email": "login@example.com", "role_code": "reviewer"})
    r = client.post("/api/v1/auth/login", json={"username": "loginme", "password": "pass1234"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_disabled_user_cannot_login(client, admin_user, admin_auth_headers):
    uid = client.post("/api/v1/admin/users", headers=admin_auth_headers, json={
        "username": "dis", "password": "pass1234", "email": "dis@example.com", "role_code": "citizen"}).json()["id"]
    client.patch(f"/api/v1/admin/users/{uid}", headers=admin_auth_headers, json={"status": "disabled"})
    r = client.post("/api/v1/auth/login", json={"username": "dis", "password": "pass1234"})
    assert r.status_code == 403


def test_admin_password_change_invalidates_existing_token(
    client, citizen_user, auth_headers, admin_user, admin_auth_headers,
):
    response = client.patch(
        f"/api/v1/admin/users/{citizen_user.id}",
        headers=admin_auth_headers,
        json={"password": "newpass5678"},
    )

    assert response.status_code == 200
    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 401
