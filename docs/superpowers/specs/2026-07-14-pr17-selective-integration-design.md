# PR #17 选择性集成设计

## 背景

PR #17 `feat/frontend-field-alignment` 包含个人资料、布局、业务页面、路由和统计改动，但它与当前 `main` 的邮件认证、系统公告和违章列表修复发生冲突。PR 中还包含错误的认证端点、浏览器本地公告和规则兜底、无效的批量通过请求体以及重复的 `contracts.ts`。

本次不合并或 cherry-pick PR 提交，而是从当前 `main` 选择性迁移已确认功能。当前 `main` 的邮件注册、找回密码、公告铃铛、`auth.js` 和 `contracts.js` 必须保持兼容。

## 目标

1. 重做个人资料页，支持修改手机号、邮箱和密码，并为管理员、审核员、市民提供默认头像。
2. 统一三个角色布局的头部操作，增加面包屑、可靠的页面缓存、返回顶部、全局错误边界和 Dashboard 深色模式。
3. 改善车辆管理、数据导出、批量驳回、规则管理和公告管理。
4. 删除驾驶人管理和数据库维护入口，管理员案件详情复用审核端 `CaseDetail`。
5. 将道路时段热力图的日期范围过滤字段从 `Violation.occurred_at` 改为 `Violation.created_at`。
6. 在完整测试通过后，将选择性集成分支 fast-forward 合入本地 `main`。

## 非目标

- 不执行 PR merge 或 cherry-pick。
- 不迁移 PR 的 TypeScript 改造，不新增 `contracts.ts`，不替换当前邮件认证实现。
- 不使用 `localStorage` 保存公告或规则。
- 不增加公告草稿或发布状态；保存后的公告立即对用户可见。
- 不实现批量通过。
- 不改变单案通过、单案驳回和邮件验证的现有后端契约。

## 集成策略

从当前 `main` 创建独立 worktree 和 `codex/pr17-selective-integration` 分支。实现过程中只参考 PR 文件内容，按当前接口和测试重新实现。每项功能使用测试驱动开发，提交保持按功能边界拆分。最终比较 `main...codex/pr17-selective-integration`，确认没有超出本文范围的改动后 fast-forward 合入本地 `main`。

## 架构与组件

### 个人资料

`Profile.vue` 负责展示角色头像、用户名、角色、手机号和邮箱，并提供资料编辑和密码修改对话框。头像使用 `public/images/admin.jpg`、`reviewer.jpg` 和 `citizen.jpg`。

当前 `UserOut` 不返回手机号和邮箱。后端扩展认证资料响应，使 `/auth/me` 和 `/auth/profile` 返回 `phone`、`email`，登录响应继续兼容现有字段。资料保存只提交允许修改的手机号和邮箱；邮箱继续执行标准化和唯一性检查。密码修改成功后清除会话并跳转登录页。

### 公共头部与布局

新增 `HeaderActions.vue`，统一承载：

- 现有 `AnnouncementBell`；
- 深色模式切换；
- 可选角色标签；
- 当前用户名；
- 个人资料导航；
- 退出登录确认。

`AdminLayout.vue`、`ReviewLayout.vue` 和 `CitizenLayout.vue` 只保留各自菜单、折叠、面包屑和内容容器逻辑，并共同使用 `HeaderActions` 和 `BackToTop`。

管理员菜单收敛为违章管理、车辆管理、用户管理、设备管理、系统配置和系统日志。审核员菜单使用平铺结构。面包屑由路由元数据和少量父级映射生成，动态案件详情应保持正确的父级入口。

### 页面缓存

需要缓存的列表和仪表盘路由使用 `meta.keepAlive: true`。布局使用常驻 `KeepAlive` 容器，根据 `route.meta.keepAlive` 决定组件进入缓存或直接渲染，不使用 route name 作为组件 `include` 白名单，从而避免路由名和 SFC 组件名不一致导致缓存失效。个人资料、编辑表单和案件详情不缓存。

### 返回顶部与错误边界

`BackToTop.vue` 接收或定位当前布局的主滚动容器，监听滚动并在阈值后显示图标按钮；卸载时移除监听。三个布局各自只挂载一个实例。

`App.vue` 使用 `onErrorCaptured` 提供全局渲染错误兜底，显示刷新操作和可诊断错误信息；正常路径只渲染路由出口。错误边界不吞掉网络错误，网络错误继续由 Axios interceptor 处理。

### Dashboard 深色模式

Dashboard 从主题 store 派生图表颜色。主题变化时重新设置 ECharts option，覆盖坐标轴、网格线、图例、提示框和文本颜色。图表实例在组件卸载时释放，窗口 resize 监听也必须清理。

## 业务页面

### 车辆管理

车辆列表按 `owner_id` 映射市民用户名。页面按后端允许的 `page_size=100` 分页获取全部 `role=citizen` 用户，用于表格显示和可搜索下拉框。新增和编辑均使用市民选择器，提交仍使用现有 `owner_id` 契约。用户列表或车辆列表请求失败时，不显示伪造的车主数据。

### Excel 导出

增加 `xlsx` 依赖和通用导出工具。管理员违章、审核员违章、市民违章和市民举报页面按当前筛选条件循环读取所有分页结果，再生成 Excel。空结果禁用导出；任一分页请求失败则终止，不生成残缺文件。导出期间按钮显示 loading，并阻止重复请求。

### 批量驳回

审核工作台增加批量选择模式，但不提供批量通过。只有后端允许审核的状态可选。用户必须输入统一驳回原因，前端逐案调用现有 `rejectCase(id, { reject_reason })`，通过 `Promise.allSettled` 汇总结果。成功案件从选择中移除，失败案件保留，页面显示成功和失败数量并刷新列表。

### 公告管理

公告以现有后端 API 为唯一数据源。管理页实现分页列表、新增、编辑和删除，字段仅为标题和正文。新增或编辑成功后刷新列表；删除最后一条导致当前页为空时返回上一页。删除需要二次确认。公告保存后立即对所有用户可见，不新增 `is_published`。

### 规则管理

现有新增、列表、编辑和启停功能继续使用后端。新增管理员接口 `DELETE /api/v1/admin/rules/{rule_id}`，成功返回 `204`，不存在返回 `404`，非管理员返回 `401/403`。前端增加删除确认和 loading 状态。删除为物理删除；临时下线继续使用 `is_active`。规则请求失败时不回退到浏览器缓存，也不显示虚假成功。

## 路由精简

删除 `/admin/drivers`、`/admin/database` 路由及 `DriverList.vue`、`DatabaseMaintain.vue` 占位页面。管理员 `/admin/violations/:id` 使用 `views/review/CaseDetail.vue`。`CaseDetail` 根据当前角色和路由返回管理员违章列表或审核工作台，避免写死审核员路径。

## 后端统计语义

`StatisticsService.road_time_heatmap` 的开始和结束日期过滤使用 `Violation.created_at`。时段分桶仍使用 `extract("hour", Violation.occurred_at)`，即统计“指定入库日期范围内的违章，在实际发生时间上的小时分布”。测试必须同时固定过滤字段和分桶字段，防止以后混淆。

## 错误处理

- Axios interceptor 继续负责通用 HTTP 和网络错误提示。
- 页面只显示需要业务上下文的错误，例如批量驳回部分失败和导出中断。
- 编辑请求失败时对话框保持打开，用户输入不丢失。
- 状态开关失败时回滚到原值。
- 删除失败时保留当前列表和分页。
- 不捕获并忽略后端错误后继续写入本地状态。

## 测试策略

所有行为遵循红、绿、重构循环。

前端 Node 测试覆盖：

- 个人资料 API 字段和密码修改后的退出行为；
- 公告与规则的精确 API 路径和 payload；
- 规则删除入口；
- 公共 HeaderActions 在三个布局中的使用；
- `meta.keepAlive` 和布局缓存结构；
- 驾驶人、数据库路由与页面删除；
- 管理员案件详情复用 `CaseDetail`；
- 全量分页导出、空数据和中途失败；
- 批量驳回的 `{ reject_reason }`、部分成功和重复提交保护；
- 当前邮件注册、找回密码、公告铃铛和 `contracts.js` 回归。

后端 pytest 覆盖：

- `/auth/me` 与 `/auth/profile` 返回手机号和邮箱；
- 规则删除的服务层行为及 `204/401/403/404`；
- 热力图使用 `created_at` 过滤、`occurred_at` 分桶；
- 完整既有后端回归。

完成验证命令：

```powershell
npm test
npm run build
uv run --cache-dir .uv-cache --extra dev pytest -q --basetemp .pytest-tmp
```

UI 冒烟测试覆盖桌面和移动视口下的三个布局、个人资料、公告、规则、车辆、审核工作台和 Dashboard 深色模式，检查菜单、面包屑、文本溢出、弹窗、返回顶部和图表颜色。

## 验收标准

1. 当前邮件认证和公告铃铛测试继续通过。
2. 所有新增页面只读取和修改后端真实数据。
3. 批量审核界面没有批量通过入口，批量驳回发送正确 payload 并报告部分失败。
4. 规则和公告具备已确认的后端 CRUD 行为。
5. 被删除路由不可访问，管理员案件详情正常复用 `CaseDetail`。
6. 热力图查询使用已确认的时间语义。
7. 前端测试、前端构建、后端测试和 UI 冒烟全部通过。
8. 集成分支 diff 不包含 PR 的认证替换、TypeScript 迁移、本地存储兜底或其他未确认改动。
