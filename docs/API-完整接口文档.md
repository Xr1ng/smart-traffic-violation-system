# 交通违章智能管理平台 · 完整接口文档

> 版本：2026-07-10 · 基地址 `http://localhost:8000`（开发）/ 生产按实际域名  
> 全局前缀：`/api/v1`（内部 AI 除外：`/internal/ai`）  
> 所有响应为强类型 JSON（无 `{code,message,data}` 信封）。鉴权失败的 HTTP 状态码即错误信息。

---

## 目录

1. [认证与用户](#1-认证与用户)
2. [权限与菜单](#2-权限与菜单)
3. [图片接入](#3-图片接入)
4. [案件审核](#4-案件审核)
5. [违章查询](#5-违章查询)
6. [统计分析](#6-统计分析)
7. [系统管理](#7-系统管理)
8. [内部 AI](#8-内部-ai)
9. [LLM 分析报告](#9-llm-分析报告)
10. [通用约定](#10-通用约定)

---

## 1. 认证与用户

前缀：`/api/v1/auth`

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|:--:|------|
| POST | `/auth/login` | 无 | 登录 |
| POST | `/auth/register` | 无 | 注册（citizen 角色） |
| GET | `/auth/me` | 登录 | 获取当前用户 |
| PUT | `/auth/profile` | 登录 | 修改个人资料 |
| PUT | `/auth/password` | 登录 | 修改密码 |

### POST /auth/login

```json
// 请求
{ "username": "admin", "password": "admin1234" }

// 200
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "username": "admin", "role_code": "admin" }
}

// 401: 用户名或密码错误
// 403: 用户已禁用
```

### POST /auth/register

```json
// 请求
{ "username": "citizen1", "password": "pass1234", "phone": "1380000", "email": "c@e.com" }

// 201 → TokenResponse（同 login）
// 409: 用户名已存在
```

### GET /auth/me

```json
// 200
{ "id": 1, "username": "admin", "role_code": "admin" }
// 401: 未登录或 token 过期
```

### PUT /auth/profile

```json
// 请求 (全 optional，只提交要改的字段)
{ "phone": "1390000", "email": "new@e.com" }

// 200 → UserOut
```

### PUT /auth/password

```json
// 请求
{ "old_password": "old", "new_password": "new" }

// 200: { "message": "密码修改成功" }
// 400: 原密码错误
```

---

## 2. 权限与菜单

前缀：`/api/v1/permissions`

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|:--:|------|
| GET | `/permissions/menus` | 登录 | 当前角色菜单 |

### GET /permissions/menus

```json
// 200 (admin)
{ "menus": ["review_workbench", "violations_query", "system_management", "statistics"] }

// 200 (citizen)
{ "menus": ["citizen_report", "my_violations"] }
```

---

## 3. 图片接入

前缀：`/api/v1/intakes`

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|:--:|------|
| POST | `/intakes/citizen-reports` | citizen | 市民随手拍 |
| POST | `/intakes/camera-captures` | X-Camera-Key | 摄像头抓拍 |
| POST | `/intakes/admin-uploads` | admin/reviewer | 管理员上传 |

### POST /intakes/citizen-reports

`Content-Type: multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| image | file | 是 | 图片文件（≤10MB，jpg/png/webp） |
| location_text | string | 否 | 拍摄地点 |

```json
// 200
{ "case_id": 1, "case_no": "CASE20260710001", "status": "uploaded",
  "message": "图片已接收，等待处理" }
```

### POST /intakes/camera-captures

Headers: `X-Camera-Key: <设备 API Key>`

参数同上，额外：

| 参数 | 类型 | 说明 |
|------|------|------|
| speed | float | 车速 km/h（超速判定用） |

**获取 Key**：见 §7 摄像头管理 `POST /admin/cameras/{id}/keys`。

### POST /intakes/admin-uploads

同 citizen，需 admin/reviewer JWT。

---

## 4. 案件审核

前缀：`/api/v1/cases`，鉴权：admin/reviewer

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/cases` | 列表（分页+筛选） |
| GET | `/cases/{id}` | 详情 |
| POST | `/cases/{id}/approve` | 审核通过 |
| POST | `/cases/{id}/reject` | 驳回 |
| POST | `/cases/{id}/request-recheck` | 重新 AI 初审 |

### GET /cases

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码（≥1） |
| page_size | int | 每页（1-100，默认 20） |
| status | string | 按状态筛选 |
| source_type | string | citizen/camera/admin |

```json
// 200
{
  "items": [{ "case_no": "CASE001", "status": "pending_human_review", ... }],
  "total": 100, "page": 1, "page_size": 20
}
```

### GET /cases/{id}

```json
// 200
{
  "id": 1, "case_no": "CASE001", "status": "pending_human_review",
  "source_type": "camera", "plate_no": null, "violation_type": null,
  "intake_event": { ... }, "media": [{ ... }],
  "ai_detection_result": null, "violation_rule_result": null, "ai_review_result": null,
  "review": {}
}
// 404: 案件不存在
```

### POST /cases/{id}/approve

```json
// 请求
{
  "plate_no": "京A12345",
  "violation_type": "超速",
  "fine_amount": 200,
  "points": 3,
  "review_opinion": "证据清晰"
}

// 200: { "violation_no": "VIO...", "notification_status": "sent", "reward_id": null }
// 400: 案件状态不可审核（仅 pending_human_review 可过）
```

### POST /cases/{id}/reject

```json
// 请求
{ "reject_reason": "证据不足" }
// 200
```

### POST /cases/{id}/request-recheck

```json
// 200
{ "message": "已重新提交 AI 识别" }
```

---

## 5. 违章查询

前缀：`/api/v1`

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|:--:|------|
| GET | `/violations` | admin/reviewer | 列表 |
| GET | `/violations/{id}` | admin/reviewer | 详情 |
| GET | `/owners/{owner_id}/violations` | 登录 | 车主违章 |

### GET /violations

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页（≤100） |
| plate_no | string | — | 车牌模糊搜索 |
| violation_type | string | — | 违章类型 |
| status | string | — | 状态 |

```json
// 200
{
  "items": [{
    "id": 1, "violation_no": "VIO001", "case_id": 1, "plate_no": "京A12345",
    "violation_type": "超速", "fine_amount": 200, "points": 3, "status": "pending",
    "occurred_at": "2026-07-10T10:00:00", "location_text": "中山大道"
  }],
  "total": 10, "page": 1, "page_size": 20
}
```

### GET /owners/{owner_id}/violations

citizen 只能看自己的；admin 可看任意。查他人→403。

---

## 6. 统计分析

前缀：`/api/v1/statistics`，鉴权：admin/reviewer

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/statistics/overview` | 案件管线概览 |
| GET | `/statistics/by-location` | 违章地点分布 |
| GET | `/statistics/by-type` | 违章类型分布 |
| GET | `/statistics/by-time` | 违章时间趋势 |

全部支持 `?start_time=...&end_time=...`（ISO 字符串）过滤时间窗口。

### GET /statistics/overview

```json
// 200
{
  "total_cases": 100, "approved_count": 60, "rejected_count": 20,
  "pending_count": 20, "approval_rate": 60.0,
  "period": { "start": "2000-01-01T00:00:00+00:00", "end": "2026-07-10T12:00:00+00:00" }
}
```

| 字段 | 说明 |
|------|------|
| total_cases | 时间窗内 Case 总数 |
| pending_count | 当前待审（**不**按时间窗过滤，全局计数） |

### GET /statistics/by-location

| 参数 | 默认 |
|------|------|
| limit | 10（≤50） |

```json
// 200
{ "items": [{ "location_text": "中山大道", "count": 45 }, ...] }
// 按 count 倒序
```

### GET /statistics/by-type

```json
// 200
{ "items": [{ "violation_type": "超速", "count": 60, "percentage": 60.0 }, ...] }
```

### GET /statistics/by-time

```json
// 200
{ "items": [{ "date": "2026-07-08", "count": 10 }, { "date": "2026-07-09", "count": 15 }] }
// 按日分组，正序
```

---

## 7. 系统管理

全部在 `/api/v1/admin` 下，鉴权：**admin**

### 7.1 用户管理

前缀：`/admin/users`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/users` | 创建 |
| GET | `/admin/users` | 列表 |
| GET | `/admin/users/{id}` | 详情 |
| PATCH | `/admin/users/{id}` | 修改 |

#### POST /admin/users

```json
// 请求
{
  "username": "reviewer1", "password": "pass1234",
  "phone": "138", "email": "r@e.com", "role_code": "reviewer"
}
// 201 → AdminUserOut
// 409: 用户名已存在 · 400: 角色不存在
```

#### GET /admin/users

| 参数 | 说明 |
|------|------|
| role | 按角色筛选（citizen/reviewer/admin/camera） |
| status | 按状态（active/disabled） |

```json
// 200
{ "items": [{ "id":1,"username":"admin","phone":null,"email":"admin@e.com",
   "role_code":"admin","role_id":3,"status":"active","created_at":"..." }],
  "total": 1, "page": 1, "page_size": 20 }
```

#### PATCH /admin/users/{id}

```json
// 请求 (全 optional)
{ "phone": "139", "email": "new@e.com", "role_code": "reviewer", "status": "disabled", "password": "newpwd" }
// 200
```

### 7.2 摄像头管理

前缀：`/admin/cameras`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/cameras` | 建设备 |
| GET | `/admin/cameras` | 列表 |
| GET | `/admin/cameras/{id}` | 详情 |
| PATCH | `/admin/cameras/{id}` | 修改 |
| POST | `/admin/cameras/{id}/keys` | 生成 Key |
| GET | `/admin/cameras/{id}/keys` | Key 列表 |
| POST | `/admin/cameras/{id}/keys/{key_id}/revoke` | 撤销 Key |

#### POST /admin/cameras

```json
// 请求
{ "device_code": "CAM-01", "location_text": "中山大道" }
// 201 → CameraDeviceOut
```

#### PATCH /admin/cameras/{id}

```json
{ "location_text": "新地点", "status": "disabled" }
// status: enabled | disabled
// disabled 后该设备的 Key 全部鉴权失败
```

#### POST /admin/cameras/{id}/keys

```json
// 201 ⚠️ raw_key 只返回这一次
{ "raw_key": "abc123xyz...", "key": { "id":1, "camera_device_id":1, "status":"active", "created_at":"..." } }
```

#### GET /admin/cameras/{id}/keys

```json
// 200 (不含 raw_key / key_hash)
{ "items": [{ "id":1, "camera_device_id":1, "status":"active", "created_at":"..." }] }
```

#### POST /admin/cameras/{id}/keys/{key_id}/revoke

```json
// 200 → key.status = "revoked"
// 撤销后该 Key 在 /intakes/camera-captures 鉴权 → 401
```

### 7.3 车辆管理

前缀：`/admin/vehicles`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/vehicles` | 录入 |
| GET | `/admin/vehicles` | 列表 |
| GET | `/admin/vehicles/{id}` | 详情 |
| PATCH | `/admin/vehicles/{id}` | 修改 |

无 DELETE。plate_no 可模糊搜索（`?plate_no=京A`）。

```json
// POST 请求
{ "plate_no": "京A12345", "owner_id": 1, "vehicle_type": "小汽车", "color": "白" }
// 409: 车牌号已存在 · 400: 车主不存在
```

### 7.4 违章规则管理

前缀：`/admin/rules`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/rules` | 建规则 |
| GET | `/admin/rules` | 列表 |
| PATCH | `/admin/rules/{id}` | 修改 |

```json
// POST
{ "rule_code": "SPD-001", "violation_type": "超速",
  "rule_type": "speed", "params": "{\"speed_limit\":80}", "description": "限速80" }
// 201

// PATCH
{ "is_active": false, "description": "已废弃" }
// rule_type: speed / special_lane
```

### 7.5 审计日志

前缀：`/admin/audit-logs`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/audit-logs` | 列表 |

| 参数 | 说明 |
|------|------|
| action | 按操作筛选（login/approve/reject/upload…） |

```json
{ "items": [{ "id":1, "user_id":1, "username":"admin", "action":"login",
   "target_type":"user", "target_id":1, "detail":"管理员登录系统",
   "ip_address":"127.0.0.1", "created_at":"..." }], "total":10, "page":1, "page_size":20 }
```

### 7.6 奖励记录

前缀：`/admin/rewards`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/rewards` | 列表 |

```json
{ "items": [{ "id":1, "citizen_id":2, "case_id":3, "violation_id":4,
   "amount":10, "reason":"举报超速成立", "status":"pending", "created_at":"..." }],
  "total":0, "page":1, "page_size":20 }
```

---

## 8. 内部 AI

前缀：`/internal/ai`（不在 `/api/v1` 下），鉴权：admin/reviewer

| 方法 | 路径 | 输入 | 说明 |
|------|------|------|------|
| POST | `/yolo/detect` | 图片文件 | YOLO 检测 |
| POST | `/ocr/plate` | 图片文件 | OCR 车牌 |
| POST | `/rules/evaluate` | JSON | 规则判定 |
| POST | `/review/text` | JSON | LLM 初审 |

### POST /internal/ai/yolo/detect

```json
// 200
{
  "objects": [{"label": "car", "confidence": 0.92, "bbox": [100,200,300,350]}],
  "vehicle_bbox": [100,200,300,350], "plate_bbox": [120,230,200,270],
  "annotated_image_url": null, "model_version": "stub-yolov8n"
}
```

### POST /internal/ai/ocr/plate

```json
// 200
{ "plate_no": "京A12345" }
// null = 识别失败
```

### POST /internal/ai/rules/evaluate

```json
// 请求
{
  "detection": { "objects": [...], "vehicle_bbox": [...], "plate_bbox": [...], "model_version": "..." },
  "ocr_result": "京A12345",
  "intake_event": { "source_type": "camera", "speed": 120, "location_text": "A" },
  "rule": { "rule_type": "speed", "rule_code": "SPD-001", "speed_limit": 80 }
}
// 200
{ "rule_matched": true, "evidence_level": "complete",
  "evidence_items": ["车速120，限速80"], "reason": "超速判定" }
```

### POST /internal/ai/review/text

```json
// 请求（自由格式 dict，服务端透传给 LLM）
{ "detection": {...}, "ocr_result": "...", "rule_result": {...}, "intake_event": {...}, "case_no": "..." }

// 200
{ "conclusion": "suggest_approve", "ai_confidence": 0.88, "reason": "..." }
// conclusion: suggest_approve / need_review / suggest_reject
```

---

## 9. LLM 分析报告

前缀：`/api/v1`，鉴权：admin/reviewer

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/analysis/reports` | 生成并保存报告 |
| GET | `/analysis/reports` | 分页查询历史报告 |
| GET | `/analysis/reports/{id}` | 获取历史报告详情 |

```json
// 请求
{ "start_time": "2026-07-01T00:00:00+08:00", "end_time": "2026-07-31T23:59:59+08:00" }
// 两个时间均必填；开始时间不得晚于结束时间，跨度不得超过 366 天

// 200
{
  "id": "a1b2c3d4e5f6",
  "title": "交通违章综合分析报告",
  "start_time": "2026-06-30T16:00:00Z",
  "end_time": "2026-07-31T15:59:59Z",
  "summary": "...",
  "trend_analysis": "...",
  "hotspot_analysis": "...",
  "risk_alerts": ["..."],
  "recommendations": ["..."],
  "statistics_snapshot": {
    "overview": {},
    "trend": [],
    "violation_types": [],
    "locations": [],
    "road_time_hotspots": []
  },
  "author": "AI 分析助手",
  "generated_at": "2026-07-13T06:00:00Z"
}
```

报告仅在 Markdown 文件原子写入成功后返回 `200`。非法日期范围返回 `422`；LLM 未配置、超时或返回格式无效时返回 `503`；报告保存失败返回 `500`。

历史列表查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `page` | int | 否 | 默认 1 |
| `page_size` | int | 否 | 默认 20，范围 1～100 |
| `start_time` | datetime | 否 | 与 `end_time` 成对提供 |
| `end_time` | datetime | 否 | 返回统计周期与查询周期存在交集的报告 |

```json
// GET /analysis/reports?page=1&page_size=20
{
  "items": [
    {
      "id": "a1b2c3d4e5f6",
      "title": "交通违章综合分析报告",
      "start_time": "2026-06-30T16:00:00Z",
      "end_time": "2026-07-31T15:59:59Z",
      "generated_at": "2026-07-13T06:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

`GET /analysis/reports/{id}` 返回与生成接口相同的完整报告结构。ID 不存在或格式非法返回 `404`；文件损坏返回 `500`。接口不会返回服务器文件路径或原始 Markdown。

历史报告由 admin/reviewer 共享，不记录发起用户，不提供修改、删除或下载 Markdown 接口。文件目录由 `REPORT_STORAGE_DIR` 配置，默认 `./reports`，报告永久保留并视为只读。

---

## 10. 通用约定

### 鉴权

| 状态码 | 含义 |
|:--:|------|
| 401 | 未登录 / token 无效 / 过期 |
| 403 | 已登录但角色不足 |

JWT 格式：`Authorization: Bearer <token>`，过期时间默认 60 分钟。

### 分页

所有列表接口统一返回：

```json
{ "items": [...], "total": N, "page": M, "page_size": S }
```

查询参数：`page`（默认 1，≥1）`page_size`（默认 20，≤100）。

### 错误

HTTP 状态码即错误类型，响应体格式：

```json
{ "detail": "错误描述" }
```

### 角色权限矩阵

| 接口组 | citizen | reviewer | admin | camera |
|------|:--:|:--:|:--:|:--:|
| /auth（login/register/me） | ✅ | ✅ | ✅ | — |
| /intakes/citizen-reports | ✅ | — | — | — |
| /intakes/camera-captures | — | — | — | ✅(Key) |
| /intakes/admin-uploads | — | ✅ | ✅ | — |
| /cases | — | ✅ | ✅ | — |
| /violations | — | ✅ | ✅ | — |
| /owners/{id}/violations | 自己 | ✅ | ✅ | — |
| /statistics | — | ✅ | ✅ | — |
| /admin/cameras | — | — | ✅ | — |
| /admin/users | — | — | ✅ | — |
| /admin/vehicles | — | — | ✅ | — |
| /admin/rules | — | — | ✅ | — |
| /admin/audit-logs | — | — | ✅ | — |
| /admin/rewards | — | — | ✅ | — |
| /internal/ai | — | ✅ | ✅ | — |
| /analysis/reports | — | ✅ | ✅ | — |

### 本地测试账号

| 用户名 | 密码 | 角色 |
|------|------|------|
| admin | admin1234 | 管理员（全权限） |

seed_data 已建。公民/审核员需通过 admin 在 `/admin/users` 创建，或用 `/auth/register` 注册。

---

> **总计 14 个模块、44 个端点。**  
> 完整代码：`backend/app/api/v1/*.py` + `backend/app/ai/routes.py`  
> Schema 定义：`backend/app/schemas/*.py`
