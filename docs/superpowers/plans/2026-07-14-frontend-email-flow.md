# Frontend Email Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the frontend registration demo code with real email verification and add a complete forgot-password/reset-password page backed by the existing API.

**Architecture:** Authentication request functions remain in `src/api/auth.js`; page-local state owns loading, countdowns, validation, and navigation. A new public `ForgotPassword.vue` implements a two-stage flow without persisting email, code, or password outside component memory.

**Tech Stack:** Vue 3 Composition API, Vue Router 4, Element Plus, Axios, Vite, Node test runner.

## Global Constraints

- Frontend only; do not modify backend files or API behavior.
- Registration uses `POST /auth/register/email-code` and sends `verification_code` to `POST /auth/register`.
- Password recovery uses `POST /auth/password-reset/email-code` and `POST /auth/password-reset`.
- Never generate, compare, log, or persist a verification code in the browser.
- Never put email, verification code, or password in URLs, local storage, session storage, or Pinia.
- Password-reset email requests always show neutral copy and must not reveal whether an account exists.
- Reuse the existing authentication layout and visual language.
- Add a new test file; do not edit the unrelated in-progress changes in `tests/contracts.test.js`.
- Follow red-green-refactor for every production change.

---

### Task 1: Authentication API Contract

**Files:**
- Create: `smart-traffic-frontend/tests/email-auth-flow.test.js`
- Modify: `smart-traffic-frontend/package.json`
- Modify: `smart-traffic-frontend/src/api/auth.js`

**Interfaces:**
- Produces: `sendRegisterEmailCode(data) -> request.post('/auth/register/email-code', data)`.
- Produces: `sendPasswordResetEmailCode(data) -> request.post('/auth/password-reset/email-code', data)`.
- Produces: `resetPassword(data) -> request.post('/auth/password-reset', data)`.

- [ ] **Step 1: Write the failing API contract test**

Create a Node test that reads `src/api/auth.js` and asserts exact exports and paths:

```js
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8')

test('auth API exposes email verification and reset endpoints', () => {
  const source = read('src/api/auth.js')
  assert.match(source, /export const sendRegisterEmailCode = \(data\) => request\.post\('\/auth\/register\/email-code', data\)/)
  assert.match(source, /export const sendPasswordResetEmailCode = \(data\) => request\.post\('\/auth\/password-reset\/email-code', data\)/)
  assert.match(source, /export const resetPassword = \(data\) => request\.post\('\/auth\/password-reset', data\)/)
})
```

Change `package.json` to run both test files exactly:

```json
"test": "node --test tests/contracts.test.js tests/email-auth-flow.test.js"
```

- [ ] **Step 2: Run the test and verify RED**

Run: `cd smart-traffic-frontend && npm test`

Expected: FAIL because the three exports do not exist.

- [ ] **Step 3: Add the three API functions**

```js
export const sendRegisterEmailCode = (data) => request.post('/auth/register/email-code', data)
export const sendPasswordResetEmailCode = (data) => request.post('/auth/password-reset/email-code', data)
export const resetPassword = (data) => request.post('/auth/password-reset', data)
```

- [ ] **Step 4: Run the test and verify GREEN**

Run: `cd smart-traffic-frontend && npm test`

Expected: all existing contract tests plus the new API contract pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add smart-traffic-frontend/package.json smart-traffic-frontend/src/api/auth.js smart-traffic-frontend/tests/email-auth-flow.test.js
git commit -m "feat(frontend): add email auth API clients"
```

### Task 2: Registration Email Verification

**Files:**
- Modify: `smart-traffic-frontend/tests/email-auth-flow.test.js`
- Modify: `smart-traffic-frontend/src/views/auth/Register.vue`

**Interfaces:**
- Consumes: `sendRegisterEmailCode({ email })` and `register(payload)`.
- Produces: real send loading, success-only countdown, timer cleanup, and registration payload with `verification_code`.

- [ ] **Step 1: Add failing registration behavior contracts**

```js
test('registration delegates verification to the backend', () => {
  const source = read('src/views/auth/Register.vue')
  assert.match(source, /sendRegisterEmailCode\(\{ email: form\.email \}\)/)
  assert.match(source, /verification_code: form\.verification_code/)
  assert.match(source, /:loading="codeLoading"/)
  assert.match(source, /onBeforeUnmount\(stopCountdown\)/)
  assert.doesNotMatch(source, /Math\.random|sentCode|演示模式|前端验证码校验/)
  assert.match(source, /await sendRegisterEmailCode[\s\S]*startCountdown\(\)/)
})
```

- [ ] **Step 2: Run the registration contract and verify RED**

Run: `cd smart-traffic-frontend && node --test tests/email-auth-flow.test.js`

Expected: FAIL on demo code, missing API call, missing payload field, and missing cleanup.

- [ ] **Step 3: Implement the registration flow**

Import `onBeforeUnmount` and `sendRegisterEmailCode`. Replace the demo state with:

```js
const codeLoading = ref(false)
const countdown = ref(0)
let countdownTimer = null

function stopCountdown() {
  if (countdownTimer !== null) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

function startCountdown() {
  stopCountdown()
  countdown.value = 60
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) stopCountdown()
  }, 1000)
}

onBeforeUnmount(stopCountdown)
```

Implement sending only after email field validation:

```js
async function handleSendCode() {
  const valid = await formRef.value.validateField('email').then(() => true).catch(() => false)
  if (!valid || codeLoading.value || countdown.value > 0) return
  codeLoading.value = true
  try {
    await sendRegisterEmailCode({ email: form.email })
    ElMessage.success('验证码已发送，请查收邮件')
    startCountdown()
  } catch (_) {
    // request interceptor displays the backend detail or network fallback
  } finally {
    codeLoading.value = false
  }
}
```

Bind `:loading="codeLoading"`, remove all client-generated-code logic, and add `verification_code: form.verification_code` to the registration request.

- [ ] **Step 4: Run registration and full frontend tests**

Run: `cd smart-traffic-frontend && npm test`

Expected: PASS and no demo-code contract failure.

- [ ] **Step 5: Commit Task 2**

```bash
git add smart-traffic-frontend/src/views/auth/Register.vue smart-traffic-frontend/tests/email-auth-flow.test.js
git commit -m "feat(frontend): connect registration email verification"
```

### Task 3: Forgot Password Page and Public Route

**Files:**
- Create: `smart-traffic-frontend/src/views/auth/ForgotPassword.vue`
- Modify: `smart-traffic-frontend/src/views/auth/Login.vue`
- Modify: `smart-traffic-frontend/src/router/index.js`
- Modify: `smart-traffic-frontend/tests/email-auth-flow.test.js`

**Interfaces:**
- Consumes: `sendPasswordResetEmailCode({ email })`, `resetPassword({ email, verification_code, new_password })`.
- Produces: public route `/forgot-password` with two stages and login navigation.

- [ ] **Step 1: Add failing route and page contracts**

```js
test('forgot password route and login entry are wired', () => {
  const router = read('src/router/index.js')
  const login = read('src/views/auth/Login.vue')
  assert.match(router, /path: '\/forgot-password'/)
  assert.match(router, /name: 'ForgotPassword'/)
  assert.match(router, /ForgotPassword\.vue/)
  assert.match(login, /router\.push\('\/forgot-password'\)/)
})

test('forgot password page sends and resets without persistence', () => {
  const source = read('src/views/auth/ForgotPassword.vue')
  assert.match(source, /sendPasswordResetEmailCode\(\{ email: form\.email \}\)/)
  assert.match(source, /resetPassword\(\{[\s\S]*email: form\.email,[\s\S]*verification_code: form\.verification_code,[\s\S]*new_password: form\.new_password/)
  assert.match(source, /onBeforeUnmount\(stopCountdown\)/)
  assert.match(source, /sendLoading/)
  assert.match(source, /resetLoading/)
  assert.match(source, /两次密码不一致/)
  assert.doesNotMatch(source, /localStorage|sessionStorage|useUserStore/)
})
```

- [ ] **Step 2: Run page contracts and verify RED**

Run: `cd smart-traffic-frontend && node --test tests/email-auth-flow.test.js`

Expected: FAIL because the page, route, and API usage do not exist.

- [ ] **Step 3: Create the two-stage page**

Use `step = ref('email')`, a reactive form with `email`, `verification_code`, `new_password`, and `confirm_password`, and these handlers:

```js
async function handleSendCode() {
  const valid = await formRef.value.validateField('email').then(() => true).catch(() => false)
  if (!valid || sendLoading.value || countdown.value > 0) return
  sendLoading.value = true
  try {
    await sendPasswordResetEmailCode({ email: form.email })
    step.value = 'reset'
    ElMessage.success('如果邮箱可用，验证码将发送至该邮箱')
    startCountdown()
  } catch (_) {
    // request interceptor displays the error
  } finally {
    sendLoading.value = false
  }
}

async function handleResetPassword() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  resetLoading.value = true
  try {
    await resetPassword({
      email: form.email,
      verification_code: form.verification_code,
      new_password: form.new_password
    })
    ElMessage.success('密码重置成功，请使用新密码登录')
    router.push('/login')
  } catch (_) {
    // request interceptor displays the backend detail
  } finally {
    resetLoading.value = false
  }
}
```

Use Element Plus form rules for required/format email, six-character code, minimum six-character password, and confirmation equality. Reuse the global `.auth-*` layout and the existing auth page input/button styling. Add `onBeforeUnmount(stopCountdown)`.

- [ ] **Step 4: Wire the route and login link**

Add this route immediately after `/register`:

```js
{
  path: '/forgot-password',
  name: 'ForgotPassword',
  component: () => import('@/views/auth/ForgotPassword.vue'),
  meta: { public: true, title: '忘记密码' }
}
```

Change the login link to `router.push('/forgot-password')`.

- [ ] **Step 5: Run frontend tests and production build**

Run: `cd smart-traffic-frontend && npm test`

Expected: PASS.

Run: `cd smart-traffic-frontend && npm run build`

Expected: Vite build exits 0 and emits the forgot-password view chunk.

- [ ] **Step 6: Commit Task 3**

```bash
git add smart-traffic-frontend/src/views/auth/ForgotPassword.vue smart-traffic-frontend/src/views/auth/Login.vue smart-traffic-frontend/src/router/index.js smart-traffic-frontend/tests/email-auth-flow.test.js
git commit -m "feat(frontend): add forgot password flow"
```

### Task 4: Final Regression and Scope Verification

**Files:**
- Verify all files modified in Tasks 1-3.

**Interfaces:**
- Verifies all frontend email-flow contracts and compilation.

- [ ] **Step 1: Run all frontend tests**

Run: `cd smart-traffic-frontend && npm test`

Expected: all tests pass.

- [ ] **Step 2: Run production build**

Run: `cd smart-traffic-frontend && npm run build`

Expected: build exits 0 without Vue template or import errors.

- [ ] **Step 3: Scan for demo and persistence regressions**

Run: `rg -n "演示模式|Math\.random|sentCode|localStorage|sessionStorage" smart-traffic-frontend/src/views/auth/Register.vue smart-traffic-frontend/src/views/auth/ForgotPassword.vue`

Expected: no output.

- [ ] **Step 4: Verify diff scope**

Run: `git diff --check && git status --short`

Expected: no backend changes; only the planned frontend files and generated ignored build output are present.

- [ ] **Step 5: Commit any final test-only corrections**

```bash
git add smart-traffic-frontend
git commit -m "test(frontend): verify email authentication flow"
```

## Final Verification

- [ ] Confirm `npm test` passes with both `contracts.test.js` and `email-auth-flow.test.js`.
- [ ] Confirm `npm run build` passes.
- [ ] Confirm registration contains no client-side generated-code logic.
- [ ] Confirm the forgot-password page contains no browser persistence calls.
- [ ] Confirm no backend file changed.
