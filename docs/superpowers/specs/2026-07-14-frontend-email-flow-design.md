# 前端邮件验证码与密码重置设计

## 1. 目标与范围

将现有后端邮件验证码能力接入 Vue 前端，替换注册页的演示验证码，并提供可用的忘记密码与密码重置界面。

本次包含：

- 注册邮箱验证码真实发送。
- 注册请求提交邮箱验证码。
- 忘记密码单页两阶段流程。
- 登录页忘记密码入口、公共路由与认证 API 封装。
- 前端契约与交互逻辑测试。

本次不包含：

- 修改个人资料邮箱时的验证码验证。
- 前端查看通知发送日志。
- 自动登录或在浏览器持久化重置流程。
- 后端接口、数据库或邮件发送规则变更。

## 2. API 接入

`smart-traffic-frontend/src/api/auth.js` 新增三个函数：

- `sendRegisterEmailCode(data)` -> `POST /auth/register/email-code`
- `sendPasswordResetEmailCode(data)` -> `POST /auth/password-reset/email-code`
- `resetPassword(data)` -> `POST /auth/password-reset`

现有 `register(data)` 保持路径不变，但调用方必须提交：

```json
{
  "username": "newuser",
  "password": "pass1234",
  "email": "user@example.com",
  "verification_code": "123456"
}
```

前端不生成、保存或比对验证码。验证码是否正确、过期或已使用完全由后端决定。

## 3. 注册页

保留现有注册页布局、字段和视觉样式，仅替换验证码行为：

1. 用户填写格式有效的邮箱。
2. 点击“获取验证码”时先单独校验邮箱字段。
3. 按钮进入发送 loading，调用 `sendRegisterEmailCode({ email })`。
4. 仅在后端返回 `202` 后显示“验证码已发送”并开始 60 秒倒计时。
5. 发送失败不启动倒计时，按钮恢复可用，展示后端 `detail` 或稳定兜底文案。
6. 注册时不再执行前端验证码比较，将 `verification_code` 原样提交给后端。

页面卸载时清除倒计时 timer，避免离开页面后继续更新组件状态。重复点击由 loading、倒计时和后端冷却共同约束。

## 4. 忘记密码页

新增 `smart-traffic-frontend/src/views/auth/ForgotPassword.vue`，路由为 `/forgot-password`，属于未登录可访问的公共页面。页面沿用登录和注册页的左右分栏、品牌区域和表单样式。

### 4.1 第一阶段：发送验证码

- 显示邮箱输入框和“发送验证码”主按钮。
- 邮箱通过必填与格式校验后调用 `sendPasswordResetEmailCode({ email })`。
- 后端无论邮箱状态均返回中性 `202`，前端统一显示“如果邮箱可用，验证码将发送至该邮箱”。
- 成功后进入第二阶段并启动 60 秒倒计时。
- 提供返回登录页的明确入口。

### 4.2 第二阶段：重置密码

- 保留邮箱只读展示。
- 显示验证码、新密码、确认密码字段。
- 验证码必须为 6 位；密码至少 6 位；两次密码必须一致。
- 支持重新发送验证码，复用第一阶段邮箱；仅发送成功后重启倒计时。
- 提交调用 `resetPassword({ email, verification_code, new_password })`。
- 成功后显示“密码重置成功，请使用新密码登录”，跳转 `/login`。
- 失败时停留当前阶段，不清空用户输入，展示后端 `detail` 或兜底文案。

邮箱、验证码和新密码不写入 URL、`localStorage`、`sessionStorage` 或全局 store。刷新页面会重新开始流程。

## 5. 路由与登录入口

- 在 `src/router/index.js` 注册 `/forgot-password`，`meta.public = true`。
- 登录页“忘记密码？”跳转 `/forgot-password`，不再跳转注册页。
- 公共路由守卫保持现有语义：已登录用户访问忘记密码页仍可进入，只有访问 `/login` 时才自动跳转角色首页。

## 6. 状态与错误处理

注册页与忘记密码页分别维护自己的发送 loading、提交 loading、倒计时和 timer。API 封装只负责请求，不包含页面状态。

错误展示遵循以下优先级：

1. `error.response.data.detail`
2. 页面对应的稳定中文兜底文案

找回密码发送成功文案固定使用中性表述，不能根据邮箱是否存在显示不同内容。注册发送接口可显示后端返回的邮箱已存在、冷却或发送失败信息。

## 7. 测试策略

扩展现有 Node 契约测试，覆盖：

- `auth.js` 导出三个新 API，并使用正确路径和 HTTP 方法。
- 注册页不再包含 `Math.random`、`sentCode` 或“演示模式”。
- 注册请求包含 `verification_code`。
- 注册验证码倒计时仅在发送请求成功后启动。
- 路由包含公共 `/forgot-password`。
- 登录页忘记密码入口指向 `/forgot-password`。
- 忘记密码页调用发送验证码和重置密码 API。
- 重置请求字段严格为 `email`、`verification_code`、`new_password`。
- 页面包含发送 loading、重置 loading、倒计时、密码一致性校验和 timer 清理。

运行现有前端测试与生产构建，确保新增页面可编译且没有破坏其他路由或契约。

## 8. 验收标准

- 点击注册页“获取验证码”不再显示明文演示验证码，而是调用后端邮件接口。
- 收到的验证码可用于注册，前端请求包含 `verification_code`。
- 登录页可进入忘记密码页面。
- 用户可通过邮箱验证码设置新密码并返回登录页。
- 找回密码发送阶段不泄露邮箱是否注册。
- 刷新或离开页面不会在浏览器持久化验证码或密码。
- 前端测试和生产构建通过。
- 不修改后端代码或个人资料邮箱流程。
