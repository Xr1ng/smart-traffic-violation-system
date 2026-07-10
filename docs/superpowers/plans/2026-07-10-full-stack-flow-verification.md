# 前后端全流程修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让后端全量测试、前端自动测试与生产构建全部通过，并在真实 MySQL + `uv run uvicorn` + Vite 环境中完成市民、审核员、管理员核心网页流程且无控制台错误、失败请求或错误提示。

**Architecture:** 保留现有 FastAPI service/schema/router 分层与 Vue 3 API 模块结构。后端补齐市民本人车辆与举报字段契约，修复案件状态码和 Alembic 分叉；前端用少量纯函数统一真实 API 字段映射，并用 Node 内置测试运行器覆盖请求参数和审核 payload。没有后端支持的管理页统一使用现有 `UnderDevelopment`，不继续展示可写但不持久化的 Mock。

**Tech Stack:** Python 3.12、uv、FastAPI、SQLAlchemy 2、Alembic、pytest、Vue 3、Vite 5、Node 25 `node:test`、Element Plus、ECharts

## Global Constraints

- 所有 Python 安装、测试和服务命令必须通过 `uv`：`uv sync --extra dev`、`uv run pytest`、`uv run alembic`、`uv run uvicorn`。
- 不重置现有 MySQL，不修改现有管理员密码，不创建临时管理员；浏览器管理员登录使用用户在会话中提供的凭据，密码不得写入仓库文件或日志。
- 不修改、恢复、暂存或提交主检出中用户删除的 `TEST_REPORT.md` 与 `test_all.py`。
- 前端已实现的用户流程必须使用真实 API；后端不存在的角色/公告/数据库/驾驶人管理功能使用 `UnderDevelopment`，不得保留假持久化操作。
- 每个生产代码修复前必须先运行能复现问题的失败测试或浏览器步骤；实现后先跑目标测试，再跑完整回归。
- API 的字段名和状态码以后端 Pydantic schema 与本计划为准；前端不得静默发送后端不接收的字段。
- 本地默认端口统一为 FastAPI `8000`、Vite `5173`；Vite `/api` 代理默认指向 `http://127.0.0.1:8000`。

---

### Task 1: 后端状态语义与 Alembic 单 head

**Files:**
- Modify: `backend/app/api/v1/cases.py`
- Modify: `backend/tests/services/test_review_service.py`
- Create: `backend/tests/test_migrations.py`
- Modify: `backend/alembic/versions/424e8489d6c7_add_violation_rules_table.py`
- Modify: `backend/alembic/versions/c98f93f77440_add_violation_rules_table.py`
- Create: `backend/alembic/versions/7d4c9f1a2b3e_merge_violation_rule_heads.py`

**Interfaces:**
- Consumes: 现有 `ReviewService` 允许 `uploaded` 案件直接审核的方案 A 语义。
- Produces: `POST /cases/{id}/request-recheck` 返回 HTTP 202；终态 `rejected/notified` 返回 409；Alembic 只有 `7d4c9f1a2b3e` 一个 head。

- [ ] **Step 1: 增加单 head 失败测试并保留现有 202 失败测试**

```python
# backend/tests/test_migrations.py
import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_has_single_head():
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == ["7d4c9f1a2b3e"]


def _load_revision(revision: str):
    path = Path(__file__).parents[1] / "alembic" / "versions" / f"{revision}_add_violation_rules_table.py"
    spec = importlib.util.spec_from_file_location(revision, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("revisions", [
    ("424e8489d6c7", "c98f93f77440"),
    ("c98f93f77440", "424e8489d6c7"),
])
def test_duplicate_rule_revisions_upgrade_in_either_order(monkeypatch, revisions):
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))
        for revision in revisions:
            module = _load_revision(revision)
            monkeypatch.setattr(module, "op", operations)
            module.upgrade()
        assert sa.inspect(connection).get_table_names().count("violation_rules") == 1
```

- [ ] **Step 2: 运行红灯测试**

Run: `cd backend && uv run pytest tests/api/test_cases_api.py::test_request_recheck_endpoint tests/test_migrations.py -q`

Expected: request-recheck 实际 200；迁移实际有 `424e8489d6c7`、`c98f93f77440` 两个 head；在未加 guard 的历史迁移上，第二次 `create_table` 抛重复表错误。

- [ ] **Step 3: 明确当前状态机回归测试**

将旧的 `test_approve_wrong_state_409` 改为终态测试，案件状态使用 `rejected`；新增 `test_approve_uploaded_state_is_allowed`，使用 `FakeNotificationProvider`，断言上传态审核会生成 `violation_no`。上传态允许审核是已合并的方案 A，不得退回旧规范。

```python
def test_approve_terminal_state_409(db, reviewer_user, citizen_user):
    from app.models.intake import Case, IntakeEvent
    ev = IntakeEvent(source_type="citizen", source_id=citizen_user.id, image_hash="terminal1")
    db.add(ev)
    db.flush()
    case = Case(case_no="CASE-TERM-1", intake_event_id=ev.id, status="rejected")
    db.add(case)
    db.commit()
    svc = ReviewService(db, FakeNotificationProvider())
    with pytest.raises(HTTPException) as exc:
        svc.approve(case.id, reviewer_user, plate_no="粤A1", violation_type="超速",
                    fine_amount=200, points=6, review_opinion="x")
    assert exc.value.status_code == 409
```

- [ ] **Step 4: 修复 202 与重复迁移**

`cases.py` 路由必须声明：

```python
@router.post("/{case_id}/request-recheck", response_model=RecheckResponse, status_code=202)
```

两个重复 `violation_rules` 迁移的 `upgrade()` 都先用 `sa.inspect(op.get_bind()).get_table_names()` 判断表是否存在；不存在才创建表和索引。`downgrade()` 同样仅在表存在时删除。新增标准 merge revision：

```python
"""merge duplicate violation rule heads"""
from typing import Sequence, Union

revision: str = "7d4c9f1a2b3e"
down_revision: Union[str, Sequence[str], None] = ("424e8489d6c7", "c98f93f77440")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
```

- [ ] **Step 5: 验证目标测试和迁移头**

Run: `cd backend && uv run pytest tests/api/test_cases_api.py tests/services/test_review_service.py tests/test_migrations.py -q`

Expected: all pass.

Run: `cd backend && uv run alembic heads`

Expected: only `7d4c9f1a2b3e (head)`.

---

### Task 2: 市民车辆、举报字段与案件列表契约

**Files:**
- Modify: `backend/app/models/intake.py`
- Modify: `backend/app/schemas/vehicle.py`
- Modify: `backend/app/schemas/case.py`
- Modify: `backend/app/services/vehicle_service.py`
- Modify: `backend/app/services/intake_service.py`
- Modify: `backend/app/api/v1/vehicles.py`
- Modify: `backend/app/api/v1/intakes.py`
- Modify: `backend/app/api/v1/cases.py`
- Modify: `backend/app/api/v1/router.py`
- Modify: `backend/tests/api/test_vehicles_api.py`
- Modify: `backend/tests/api/test_intakes.py`
- Modify: `backend/tests/api/test_cases_api.py`
- Create: `backend/alembic/versions/8e5d0a2b4c6f_add_intake_description.py`

**Interfaces:**
- Consumes: Task 1 merge head `7d4c9f1a2b3e`。
- Produces: `GET/POST /api/v1/vehicles/me`、`DELETE /api/v1/vehicles/me/{id}`；举报保留 `captured_at` 和 `description`；案件列表包含 `source_desc`、`description`、`media.original_url`、`reward`。

- [ ] **Step 1: 写市民车辆失败 API 测试**

```python
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


def test_citizen_binds_and_unbinds_own_vehicle(client, auth_headers):
    created = client.post("/api/v1/vehicles/me", headers=auth_headers,
                          json={"plate_no": "粤C30003", "vehicle_type": "小型轿车", "color": "白"})
    assert created.status_code == 201
    vehicle_id = created.json()["id"]
    deleted = client.delete(f"/api/v1/vehicles/me/{vehicle_id}", headers=auth_headers)
    assert deleted.status_code == 204
    assert client.get("/api/v1/vehicles/me", headers=auth_headers).json()["total"] == 0
```

- [ ] **Step 2: 写举报元数据失败测试**

```python
def test_citizen_report_persists_metadata(client, db, citizen_user, auth_headers, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    response = client.post(
        "/api/v1/intakes/citizen-reports",
        headers=auth_headers,
        files={"image": ("meta.jpg", JPEG, "image/jpeg")},
        data={"location_text": "测试路口", "captured_at": "2026-07-10T08:30:00",
              "description": "车辆闯红灯"},
    )
    assert response.status_code == 200
    from app.models.intake import Case
    event = db.get(Case, response.json()["case_id"]).intake_event
    assert event.description == "车辆闯红灯"
    assert event.captured_at.isoformat().startswith("2026-07-10T08:30:00")
```

- [ ] **Step 3: 运行红灯测试**

Run: `cd backend && uv run pytest tests/api/test_vehicles_api.py tests/api/test_intakes.py -q`

Expected: `/vehicles/me` 404；举报事件没有 `description`，且 `captured_at` 未传入 service。

- [ ] **Step 4: 实现本人车辆 API**

新增 schema：

```python
class VehicleBindIn(BaseModel):
    plate_no: str
    vehicle_type: str | None = None
    color: str | None = None
```

扩展 `VehicleService.list_vehicles(..., owner_id: int | None = None)`，有 `owner_id` 时过滤；新增 `unbind_vehicle(vehicle_id, owner_id)`，非本人返回 404，本人车辆设置 `owner_id=None` 后提交。`vehicles.py` 新增 `citizen_router = APIRouter(prefix="/vehicles", tags=["vehicles"])`，三个端点都 `require_role("citizen")`，POST 的 owner_id 只能来自 token 用户。`router.py` 同时 include `vehicles.router` 与 `vehicles.citizen_router`。

- [ ] **Step 5: 实现举报元数据和列表字段**

`IntakeEvent` 新增：

```python
description: Mapped[str | None] = mapped_column(String(512))
```

`create_intake` 新增可选 `description` 并写入事件。市民举报接收 `captured_at: datetime | None = Form(None)` 和 `description: str | None = Form(None)`；后台上传接收 `captured_at`、`speed` 并传给 service。

新增迁移 `8e5d0a2b4c6f`，`down_revision="7d4c9f1a2b3e"`，upgrade 给 `intake_events` 增加 nullable `description VARCHAR(512)`，downgrade 删除该列。

`CaseListItem` 新增：

```python
source_desc: str = ""
description: str | None = None
media: dict = {}
reward: int | None = None
```

`list_cases` 从事件 media 生成 `{"original_url": url}`，从 `Reward.case_id` 批量构建奖励映射，并填充上述字段。

`GET /cases` 新增 `keyword` query；`CaseService.list_cases` 在 `case_no`、`plate_no`、`IntakeEvent.location_text` 上做同一关键字的 `ILIKE` OR 查询，且 `need_join` 在 keyword 存在时必须连接 `IntakeEvent`。新增 API 测试断言案件号和地点关键字都能命中。

- [ ] **Step 6: 运行目标回归**

Run: `cd backend && uv run pytest tests/api/test_vehicles_api.py tests/services/test_vehicle_service.py tests/api/test_intakes.py tests/services/test_intake_service.py tests/api/test_cases_api.py -q`

Expected: all pass.

---

### Task 3: 前端真实 API 契约与自动测试

**Files:**
- Modify: `smart-traffic-frontend/package.json`
- Create: `smart-traffic-frontend/src/utils/contracts.js`
- Create: `smart-traffic-frontend/tests/contracts.test.js`
- Modify: `smart-traffic-frontend/src/views/stats/Dashboard.vue`
- Modify: `smart-traffic-frontend/src/views/stats/Report.vue`
- Modify: `smart-traffic-frontend/src/views/review/CaseDetail.vue`
- Modify: `smart-traffic-frontend/src/views/review/Workbench.vue`
- Modify: `smart-traffic-frontend/src/views/admin/ViolationList.vue`
- Modify: `smart-traffic-frontend/src/views/admin/AdvancedSearch.vue`
- Modify: `smart-traffic-frontend/src/views/admin/RoleManage.vue`
- Modify: `smart-traffic-frontend/src/views/system/RoleManage.vue`
- Modify: `smart-traffic-frontend/src/views/admin/RuleConfig.vue`
- Modify: `smart-traffic-frontend/src/views/admin/SmsTemplate.vue`
- Modify: `smart-traffic-frontend/src/views/citizen/VehicleBinding.vue`
- Modify: `smart-traffic-frontend/src/views/citizen/Home.vue`
- Modify: `smart-traffic-frontend/src/views/citizen/MyReports.vue`
- Modify: `smart-traffic-frontend/src/api/vehicle.js`
- Modify: `smart-traffic-frontend/vite.config.js`

**Interfaces:**
- Consumes: Task 1 的 202/审核语义，Task 2 的 `/vehicles/me` 与扩展案件列表。
- Produces: `npm test` 覆盖统计、查询、审核 payload；所有已实现页面只读真实 API 字段；角色管理明确占位。

- [ ] **Step 1: 添加 Node 内置测试脚本和失败测试**

`package.json` scripts 新增：

```json
"test": "node --test tests/contracts.test.js"
```

`contracts.test.js` 必须覆盖：

```javascript
import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildApprovePayload, buildRejectPayload, buildViolationQuery,
  getStatisticsCards, mapNamedSeries, reportPathForRoute
} from '../src/utils/contracts.js'

test('maps backend statistics fields without multiplying percentages', () => {
  const cards = getStatisticsCards({ total_cases: 3, total_violations: 2,
    approve_rate: 66.7, reject_rate: 33.3, pending_count: 1, today_new: 2 })
  assert.deepEqual(cards.map(card => card.value), [3, 2, '66.7%', '33.3%', 1, 2])
})

test('maps name/value statistic series', () => {
  assert.deepEqual(mapNamedSeries({ items: [{ name: '超速', value: 2 }] }), [{ name: '超速', value: 2 }])
})

test('uses backend violation query names', () => {
  assert.deepEqual(buildViolationQuery({ plate: '粤A', type: '超速', location: '人民路',
    dateRange: ['2026-07-01', '2026-07-10'] }, 2, 10), {
    page: 2, page_size: 10, plate_no: '粤A', violation_type: '超速', location_text: '人民路',
    start_time: '2026-07-01T00:00:00', end_time: '2026-07-10T23:59:59'
  })
})

test('builds exact review request bodies', () => {
  const form = { action: 'approve', plate_no: '粤A1', violation_type: '超速',
    fine_amount: 200, points: 3, review_opinion: '证据清晰' }
  assert.deepEqual(buildApprovePayload(form), { plate_no: '粤A1', violation_type: '超速',
    fine_amount: 200, points: 3, review_opinion: '证据清晰' })
  assert.deepEqual(buildRejectPayload(form), { reject_reason: '证据清晰' })
})

test('keeps admin report navigation inside admin routes', () => {
  assert.equal(reportPathForRoute('/admin/stats'), '/admin/stats/report')
  assert.equal(reportPathForRoute('/stats'), '/stats/report')
})
```

- [ ] **Step 2: 运行红灯测试**

Run: `cd smart-traffic-frontend && npm test`

Expected: `src/utils/contracts.js` 不存在，测试失败。

- [ ] **Step 3: 实现契约纯函数并接入页面**

`contracts.js` 导出上述六个函数。统计卡片严格使用后端 `total_cases/total_violations/approve_rate/reject_rate/pending_count/today_new`；百分比不再乘 100。type/location 图直接使用 `name/value`。

`Report.vue` 展示后端 `title/content/author/generated_at`，使用 `white-space: pre-wrap`，删除不存在的 `summary/highlights/suggestions` 读取。

`CaseDetail.vue` 使用 `buildApprovePayload` 和 `buildRejectPayload`；`statusType` 默认返回 `info`，并明确 `notified: success`，消除 `ElTag type=""` 警告。

`ViolationList.vue` 与 `AdvancedSearch.vue` 使用 `buildViolationQuery`；表格字段改为 `plate_no/location_text/occurred_at`，管理员审核按钮导航 `/review/case/${row.case_id}`；删除后端不支持的驾驶员筛选。

`Dashboard.vue` 使用 `reportPathForRoute(route.path)`，管理员不会被 `/stats/report` 的 reviewer-only 守卫弹回。

- [ ] **Step 4: 接入市民真实车辆与概览**

`vehicle.js` 新增并使用：

```javascript
export const getMyVehicles = () => request.get('/vehicles/me')
export const bindMyVehicle = (data) => request.post('/vehicles/me', data)
export const unbindMyVehicle = (id) => request.delete(`/vehicles/me/${id}`)
```

`VehicleBinding.vue` 不再调用 admin API、不再发送 owner_id；解绑必须调用真实 DELETE；移除重复的成功 toast。`Home.vue` 用 `fetchOwnerViolations`、`fetchCases`、`getMyVehicles` 填充真实计数，奖励金额从案件列表 `reward` 求和。`MyReports.vue` 图片读取 `row.media?.original_url`，补 `notified` 状态文案。

- [ ] **Step 5: 无后端角色 CRUD 页面降级**

两处 `RoleManage.vue` 都替换为：

```vue
<template><UnderDevelopment /></template>
<script setup>
import UnderDevelopment from '@/components/UnderDevelopment.vue'
</script>
```

`SmsTemplate.vue` 同样替换为 `UnderDevelopment`，因为当前后端没有模板 CRUD。`RuleConfig.vue` 必须改用 `fetchRules/createRule/updateRule`：

```javascript
const rules = ref([])
const dialog = reactive({ visible: false, isEdit: false, id: null })
const form = reactive({ rule_code: '', violation_type: '', rule_type: '', params: '', description: '' })

async function loadRules() {
  const res = await fetchRules({ page: 1, page_size: 100 })
  rules.value = res.data.items
}

async function saveRule() {
  const payload = {
    violation_type: form.violation_type,
    rule_type: form.rule_type,
    params: form.params || null,
    description: form.description || null
  }
  if (dialog.isEdit) await updateRule(dialog.id, payload)
  else await createRule({ rule_code: form.rule_code, ...payload })
  dialog.visible = false
  await loadRules()
}

async function toggleRule(row) {
  await updateRule(row.id, { is_active: row.is_active })
}
```

表格展示 `rule_code/violation_type/rule_type/params/description/is_active`；新增弹窗的 `rule_code/violation_type/rule_type` 必填，编辑时 `rule_code` 禁用且不发送。后端没有 DELETE，因此页面不得显示删除按钮。所有加载、保存和开关失败都要恢复可交互状态并显示一次错误消息。

- [ ] **Step 6: 标准化开发代理**

`vite.config.js` 的 `/api` target 使用：

```javascript
target: process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000'
```

- [ ] **Step 7: 验证前端测试和构建**

Run: `cd smart-traffic-frontend && npm test`

Expected: all pass.

Run: `cd smart-traffic-frontend && npm run build`

Expected: exit 0，无 named export、Vue 编译或模块加载错误。

---

### Task 4: 全量后端回归与 MySQL 迁移验收

**Files:**
- Modify only if a regression proves a root-cause fix is required.

**Interfaces:**
- Consumes: Tasks 1-3 全部后端改动。
- Produces: 现有 pytest 全绿、单 head、当前 MySQL 可安全升级。

- [ ] **Step 1: 跑完整后端测试**

Run: `cd backend && uv run pytest -q`

Expected: `180+ passed, 0 failed`；允许已有 Starlette/httpx 弃用警告，但不得新增应用警告。

- [ ] **Step 2: 用 MySQL 执行实际升级**

Run: `cd backend && uv run alembic upgrade head`

Expected: exit 0；不删除现有数据；`uv run alembic current` 为单 head。

---

### Task 5: 三角色真实浏览器验收

**Files:**
- Modify only if browser evidence exposes a reproducible code defect; each defect first加最小自动回归测试。

**Interfaces:**
- Consumes: FastAPI `127.0.0.1:8000`、Vite `127.0.0.1:5173`、MySQL 演示账号。
- Produces: 市民、审核员、管理员核心页面均加载成功，浏览器 console error/warn 为 0，关键 API 无 4xx/5xx。

- [ ] **Step 1: 启动服务**

Run: `cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`

Run: `cd smart-traffic-frontend && npm run dev -- --host 127.0.0.1`

- [ ] **Step 2: 市民流程**

使用 `owner1 / pass1234`：登录 → 首页真实概览 → 我的违章 → 随手拍举报表单加载；通过真实 `/intakes/citizen-reports` API 上传生成的非敏感测试 JPEG、地点、时间、描述作为验收夹具 → 浏览器举报进度显示新案件 → 车辆绑定页显示本人车辆。不得出现 403、422、网络错误或重复成功 toast。

- [ ] **Step 3: 审核员流程**

使用 `reviewer / reviewer123`：登录 → 工作台卡片含来源和原图 → 打开新案件详情 → 驳回请求 body 为 `reject_reason` 且成功；另建案件验证审核通过 → 违章记录 → 统计页显示与 API 相同的 100.0%/数量 → 报告页显示完整 content。不得出现 `ElTag type=""` Vue warning。

- [ ] **Step 4: 管理员流程**

使用用户提供的管理员凭据：登录 → 统计页及报告 → 用户、摄像头、规则、车辆、日志真实 API 页面 → 角色、公告、数据库、驾驶人页面显示 `UnderDevelopment` → 违章列表字段完整且“审核”进入 `/review/case/{case_id}`。不得出现路由回弹、403、404、422 或 console error/warn。

- [ ] **Step 5: 最终证据**

Run: `cd backend && uv run pytest -q`

Run: `cd smart-traffic-frontend && npm test && npm run build`

Run: `git status --short` and `git diff --check`

Expected: 全部 exit 0；仅任务文件有预期修改；浏览器三角色日志无错误或警告。

---

## Self-Review

- Spec coverage: 覆盖后端现有 2 个失败、Alembic 双 head、统计/报告字段、审批/驳回 payload、管理员错误路由、市民车辆 403、举报元数据、角色 Mock 和三角色浏览器验收。
- Placeholder scan: `UnderDevelopment` 是明确的产品降级组件，仅用于后端不存在的功能，其他步骤均给出确定接口与验证命令。
- Type consistency: `CaseListItem.media` 与前端 `row.media.original_url` 一致；车辆本人端点统一 `/vehicles/me`；统计系列统一 `{name,value}`；审核 body 与 Pydantic schema 精确一致。
