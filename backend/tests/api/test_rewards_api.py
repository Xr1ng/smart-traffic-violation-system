def test_list_rewards(client, admin_user, admin_auth_headers):
    r = client.get("/api/v1/admin/rewards", headers=admin_auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()
    assert "total" in r.json()


def test_list_rewards_requires_auth(client):
    assert client.get("/api/v1/admin/rewards").status_code == 401
