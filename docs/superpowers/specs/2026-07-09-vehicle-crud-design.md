# 张浩-4 车辆/车主管理 CRU · Design Spec

## 背景
分工张浩-4 = 车辆录入/查询/绑定车主。Vehicle 模型（violation.py）：plate_no(unique)/owner_id(FK)/vehicle_type/color/created_at。无 status 字段 → CRU 无删。admin 鉴权，照杨翼 route→service→schemas 模式。phase-2。本地 main（b864625，151 passed）。

## 路由（/api/v1/admin/vehicles，全 require_role("admin")）
- POST /admin/vehicles — 建立车辆 → 201 VehicleOut
- GET /admin/vehicles — 列表（page/page_size，可选 plate_no 模糊搜）→ VehicleListResponse
- GET /admin/vehicles/{id} — 详情 → VehicleOut (404)
- PATCH /admin/vehicles/{id} — 改 plate_no/owner_id/vehicle_type/color → VehicleOut
- 无 DELETE

## Schemas（app/schemas/vehicle.py）
- VehicleOut：id/plate_no/owner_id/vehicle_type/color/created_at（from_attributes）
- VehicleCreateIn：plate_no/owner_id?/vehicle_type?/color?
- VehicleUpdateIn：plate_no?/owner_id?/vehicle_type?/color?（全 optional）
- VehicleListResponse：items/total/page/page_size

## Service（app/services/vehicle_service.py）
VehicleService(db)：create（plate_no 重复 409；owner_id 若提供则查 User 200/404？若无该 user 则 400）/list/patch

## 不做
- 硬删、不改 Vehicle 模型、不动杨翼代码（只 router 挂载）。
