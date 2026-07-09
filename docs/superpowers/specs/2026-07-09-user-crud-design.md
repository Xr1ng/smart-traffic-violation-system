# 张浩-3 用户管理 CRUD · Design Spec

## 背景
分工张浩-3 = 用户管理 CRUD（注册/列表/改/启用禁用）。phase-2（运维后台），User/Role 模型已建。照杨翼 route→service→schemas 模式，admin 鉴权，软删（status=disabled），SQLite 测试。本地 main（b864625，136 passed）。

## 路由（前缀 `/api/v1/admin/users`，全 `require_role("admin")`）
- `POST /admin/users` — 建用户（username/password/phone?/email?/role_code）→ 201 `AdminUserOut`
- `GET /admin/users` — 列表（page/page_size，可选 role/status 过滤）→ `AdminUserListResponse`
- `GET /admin/users/{id}` — 详情 → `AdminUserOut`（404）
- `PATCH /admin/users/{id}` — 改 phone/email/role_code/status/password（任选）→ `AdminUserOut`
- 无 DELETE（软禁用 status=disabled）

## Schemas（`app/schemas/user.py`）
- `AdminUserOut`：id/username/phone/email/role_code/role_id/status/created_at（from_attributes）
- `UserCreateIn`：username/password/phone?/email?/role_code
- `UserUpdateIn`：phone?/email?/role_code?/status?/password?（全 optional）
- `AdminUserListResponse`：items/total/page/page_size

## Service（`app/services/user_service.py`）
`UserService(db)`：create_user（username 重复 409；password 用 hash_password；role_code 找不到 400）/list_users（分页+过滤）/get_user（404）/update_user（404；role_code 找不到 400；password 提供则 re-hash；status 校验 active/disabled）。

## 鉴权
全 `require_role("admin")`。无 token→401、非 admin→403。

## 测试（TDD）
- `tests/services/test_user_service.py`：create（重复 409、role 不存在 400）/list 分页过滤/get 404/update（改 status/password/role）
- `tests/api/test_users_api.py`：CRUD + 鉴权（401/403/200）+ 建后能用新账号登录（端到端）

## 不做
- 硬删、不改 User/Role 模型、不动杨翼代码（只 router.py 挂载）。
