def test_create_vehicle_requires_auth(client, citizen_user):
    assert client.post("/api/v1/admin/vehicles",
                       json={"plate_no": "粤A", "owner_id": citizen_user.id}).status_code == 401


def test_create_vehicle_reviewer_forbidden(client, citizen_user, reviewer_user, reviewer_auth_headers):
    r = client.post("/api/v1/admin/vehicles", headers=reviewer_auth_headers,
                    json={"plate_no": "粤A", "owner_id": citizen_user.id})
    assert r.status_code == 403


def test_create_vehicle_success(client, citizen_user, admin_user, admin_auth_headers):
    r = client.post("/api/v1/admin/vehicles", headers=admin_auth_headers, json={
        "plate_no": "粤A123", "owner_id": citizen_user.id, "vehicle_type": "小汽车", "color": "白"})
    assert r.status_code == 201
    data = r.json()
    assert data["plate_no"] == "粤A123"
    assert data["vehicle_type"] == "小汽车"


def test_list_vehicles(client, citizen_user, admin_user, admin_auth_headers):
    client.post("/api/v1/admin/vehicles", headers=admin_auth_headers,
                json={"plate_no": "粤A", "owner_id": citizen_user.id})
    client.post("/api/v1/admin/vehicles", headers=admin_auth_headers,
                json={"plate_no": "粤B", "owner_id": citizen_user.id})
    r = client.get("/api/v1/admin/vehicles", headers=admin_auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] >= 2


def test_get_vehicle_404(client, admin_user, admin_auth_headers):
    assert client.get("/api/v1/admin/vehicles/9999", headers=admin_auth_headers).status_code == 404


def test_patch_vehicle(client, citizen_user, admin_user, admin_auth_headers):
    vid = client.post("/api/v1/admin/vehicles", headers=admin_auth_headers,
                      json={"plate_no": "粤A", "owner_id": citizen_user.id}).json()["id"]
    r = client.patch(f"/api/v1/admin/vehicles/{vid}", headers=admin_auth_headers,
                     json={"vehicle_type": "卡车", "color": "红"})
    assert r.status_code == 200
    data = r.json()
    assert data["vehicle_type"] == "卡车"
    assert data["color"] == "红"


def test_citizen_lists_only_own_vehicles(client, db, citizen_user, auth_headers, admin_user):
    from app.models.violation import Vehicle

    db.add_all([
        Vehicle(plate_no="粤A10001", owner_id=citizen_user.id),
        Vehicle(plate_no="粤B20002", owner_id=admin_user.id),
    ])
    db.commit()

    response = client.get("/api/v1/vehicles/me", headers=auth_headers)

    assert response.status_code == 200
    assert [item["plate_no"] for item in response.json()["items"]] == ["粤A10001"]


def test_citizen_binds_and_unbinds_own_vehicle(client, db, auth_headers):
    from app.models.violation import Vehicle

    created = client.post(
        "/api/v1/vehicles/me",
        headers=auth_headers,
        json={"plate_no": "粤C30003", "vehicle_type": "小型轿车", "color": "白"},
    )
    assert created.status_code == 201
    vehicle_id = created.json()["id"]

    deleted = client.delete(f"/api/v1/vehicles/me/{vehicle_id}", headers=auth_headers)

    assert deleted.status_code == 204
    assert client.get("/api/v1/vehicles/me", headers=auth_headers).json()["total"] == 0
    db.expire_all()
    vehicle = db.get(Vehicle, vehicle_id)
    assert vehicle is not None
    assert vehicle.owner_id is None


def test_citizen_cannot_unbind_another_users_vehicle(
    client, db, auth_headers, admin_user,
):
    from app.models.violation import Vehicle

    vehicle = Vehicle(plate_no="粤D40004", owner_id=admin_user.id)
    db.add(vehicle)
    db.commit()

    response = client.delete(f"/api/v1/vehicles/me/{vehicle.id}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "车辆不存在"
    db.refresh(vehicle)
    assert vehicle.owner_id == admin_user.id
