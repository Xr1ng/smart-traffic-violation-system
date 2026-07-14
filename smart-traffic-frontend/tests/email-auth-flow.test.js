import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import test from 'node:test'
import { reactive, ref } from 'vue'

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8')

const instantiateScriptSetup = (path, dependencies, exposedNames) => {
  const source = read(path)
  const script = source.match(/<script setup>([\s\S]*?)<\/script>/)?.[1]
  assert.ok(script, `${path} must contain a script setup block`)

  const executable = script.replace(/^import .*$/gm, '')
  const factory = new Function(
    ...Object.keys(dependencies),
    `${executable}\nreturn { ${exposedNames.join(', ')} }`
  )
  return factory(...Object.values(dependencies))
}

const createFakeTimers = () => {
  let nextId = 1
  const active = new Map()
  const cleared = []

  return {
    active,
    cleared,
    setInterval(callback, delay) {
      const id = nextId++
      active.set(id, { callback, delay })
      return id
    },
    clearInterval(id) {
      active.delete(id)
      cleared.push(id)
    }
  }
}

const createDeferred = () => {
  let resolve
  let reject
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

const flushTasks = () => new Promise((resolve) => setImmediate(resolve))

const createForgotPasswordRuntime = (overrides = {}) => {
  const timers = createFakeTimers()
  const notifications = []
  const navigations = []
  let cleanup

  const dependencies = {
    ref,
    reactive,
    onBeforeUnmount: (callback) => { cleanup = callback },
    useRouter: () => ({ push: (path) => navigations.push(path) }),
    ElMessage: { success: (message) => notifications.push(message) },
    sendPasswordResetEmailCode: async () => {},
    resetPassword: async () => {},
    setInterval: timers.setInterval,
    clearInterval: timers.clearInterval,
    ...overrides
  }

  const runtime = instantiateScriptSetup(
    'src/views/auth/ForgotPassword.vue',
    dependencies,
    [
      'formRef', 'step', 'sendLoading', 'resetLoading', 'countdown', 'form',
      'handleSendCode', 'handleResetPassword', 'handleChangeEmail'
    ]
  )

  runtime.formRef.value = {
    validateField: async () => true,
    validate: async () => true
  }

  return { ...runtime, cleanup: () => cleanup(), navigations, notifications, timers }
}

const createRegisterRuntime = (overrides = {}) => {
  const timers = createFakeTimers()
  const notifications = []
  const navigations = []
  let cleanup

  const dependencies = {
    ref,
    reactive,
    onBeforeUnmount: (callback) => { cleanup = callback },
    useRouter: () => ({ push: (path) => navigations.push(path) }),
    ElMessage: { success: (message) => notifications.push(message) },
    sendRegisterEmailCode: async () => {},
    register: async () => {},
    setInterval: timers.setInterval,
    clearInterval: timers.clearInterval,
    ...overrides
  }

  const runtime = instantiateScriptSetup(
    'src/views/auth/Register.vue',
    dependencies,
    [
      'formRef', 'loading', 'codeLoading', 'countdown', 'form',
      'handleSendCode', 'handleRegister'
    ]
  )

  runtime.formRef.value = {
    validateField: async () => true,
    validate: async () => true
  }

  return { ...runtime, cleanup: () => cleanup(), navigations, notifications, timers }
}

const createLoginRuntime = (overrides = {}) => {
  const notifications = []
  const navigations = []

  const dependencies = {
    ref,
    reactive,
    useRouter: () => ({ push: (path) => navigations.push(path) }),
    useUserStore: () => ({ homePath: '/admin/stats' }),
    ElMessage: { success: (message) => notifications.push(message) },
    login: async () => {},
    ...overrides
  }

  const runtime = instantiateScriptSetup(
    'src/views/auth/Login.vue',
    dependencies,
    ['formRef', 'loading', 'form', 'handleLogin']
  )

  runtime.formRef.value = { validate: async () => true }

  return { ...runtime, navigations, notifications }
}


test('auth API exposes email verification and reset endpoints', () => {
  const source = read('src/api/auth.js')

  assert.match(
    source,
    /export const sendRegisterEmailCode = \(data\) => request\.post\('\/auth\/register\/email-code', data\)/
  )
  assert.match(
    source,
    /export const sendPasswordResetEmailCode = \(data\) => request\.post\('\/auth\/password-reset\/email-code', data\)/
  )
  assert.match(
    source,
    /export const resetPassword = \(data\) => request\.post\('\/auth\/password-reset', data\)/
  )
})


test('registration delegates verification to the backend', () => {
  const source = read('src/views/auth/Register.vue')

  assert.match(source, /sendRegisterEmailCode\(\{ email: form\.email \}\)/)
  assert.match(source, /verification_code: form\.verification_code/)
  assert.match(source, /:loading="codeLoading"/)
  assert.match(source, /v-model="form\.email"[\s\S]*:readonly="codeLoading"/)
  assert.match(source, /onBeforeUnmount\((?:stopCountdown|handleUnmount)\)/)
  assert.match(source, /await sendRegisterEmailCode[\s\S]*startCountdown\(\)/)
  assert.ok(source.includes('pattern: /^\\d{6}$/'))
  assert.doesNotMatch(source, /Math\.random|sentCode|演示模式|前端验证码校验/)
})


test('forgot password route and login entry are wired', () => {
  const router = read('src/router/index.js')
  const login = read('src/views/auth/Login.vue')

  assert.match(router, /path: '\/forgot-password'/)
  assert.match(router, /name: 'ForgotPassword'/)
  assert.match(router, /ForgotPassword\.vue/)
  assert.match(login, /router\.push\('\/forgot-password'\)/)
})


test('login runtime keeps failed credentials on the login page', async () => {
  const runtime = createLoginRuntime({
    login: async () => {
      throw Object.assign(new Error('Request failed with status code 401'), {
        isAxiosError: true
      })
    }
  })
  runtime.form.username = 'admin'
  runtime.form.password = 'wrong-password'

  await runtime.handleLogin()

  assert.equal(runtime.loading.value, false)
  assert.deepEqual(runtime.navigations, [])
  assert.deepEqual(runtime.notifications, [])
})


test('forgot password page sends and resets without persistence', () => {
  const pageUrl = new URL('../src/views/auth/ForgotPassword.vue', import.meta.url)
  assert.equal(existsSync(pageUrl), true, 'ForgotPassword.vue must exist')
  const source = read('src/views/auth/ForgotPassword.vue')

  assert.match(source, /sendPasswordResetEmailCode\(\{ email: form\.email \}\)/)
  assert.match(
    source,
    /resetPassword\(\{[\s\S]*email: form\.email,[\s\S]*verification_code: form\.verification_code,[\s\S]*new_password: form\.new_password/
  )
  assert.match(source, /onBeforeUnmount\((?:stopCountdown|handleUnmount)\)/)
  assert.match(source, /sendLoading/)
  assert.match(source, /resetLoading/)
  assert.match(source, /:readonly="step === 'reset' \|\| sendLoading"/)
  assert.match(source, /两次密码不一致/)
  assert.ok(source.includes('pattern: /^\\d{6}$/'))
  assert.doesNotMatch(source, /localStorage|sessionStorage|useUserStore/)
})


test('forgot password page lets users correct the email after sending', () => {
  const source = read('src/views/auth/ForgotPassword.vue')

  assert.match(source, /@click="handleChangeEmail"/)
  assert.match(source, />更换邮箱</)
  assert.match(
    source,
    /function handleChangeEmail\(\) \{[\s\S]*stopCountdown\(\)[\s\S]*countdown\.value = 0[\s\S]*form\.verification_code = ''[\s\S]*form\.new_password = ''[\s\S]*form\.confirm_password = ''[\s\S]*step\.value = 'email'/
  )
})


test('forgot password runtime starts and cleans the countdown only after a successful send', async () => {
  const requests = []
  const runtime = createForgotPasswordRuntime({
    sendPasswordResetEmailCode: async (payload) => requests.push(payload)
  })
  runtime.form.email = 'driver@example.com'

  await runtime.handleSendCode()

  assert.deepEqual(requests, [{ email: 'driver@example.com' }])
  assert.equal(runtime.step.value, 'reset')
  assert.equal(runtime.sendLoading.value, false)
  assert.equal(runtime.countdown.value, 60)
  assert.deepEqual(runtime.notifications, ['如果邮箱可用，验证码将发送至该邮箱'])
  assert.equal(runtime.timers.active.size, 1)

  runtime.cleanup()
  assert.equal(runtime.timers.active.size, 0)
  assert.equal(runtime.timers.cleared.length, 1)
})


test('forgot password runtime keeps the email stage after a failed send', async () => {
  const runtime = createForgotPasswordRuntime({
    sendPasswordResetEmailCode: async () => { throw new Error('network') }
  })
  runtime.form.email = 'driver@example.com'

  await runtime.handleSendCode()

  assert.equal(runtime.step.value, 'email')
  assert.equal(runtime.sendLoading.value, false)
  assert.equal(runtime.countdown.value, 0)
  assert.equal(runtime.timers.active.size, 0)
  assert.deepEqual(runtime.notifications, [])
})


test('forgot password runtime keeps reset state and no countdown after a failed resend', async () => {
  const runtime = createForgotPasswordRuntime({
    sendPasswordResetEmailCode: async () => { throw new Error('network') }
  })
  runtime.form.email = 'driver@example.com'
  runtime.step.value = 'reset'

  await runtime.handleSendCode()

  assert.equal(runtime.step.value, 'reset')
  assert.equal(runtime.sendLoading.value, false)
  assert.equal(runtime.countdown.value, 0)
  assert.equal(runtime.timers.active.size, 0)
})


test('forgot password runtime suppresses duplicate sends and submits the exact reset payload', async () => {
  const sendDeferred = createDeferred()
  const resetDeferred = createDeferred()
  const sendRequests = []
  const resetRequests = []
  const runtime = createForgotPasswordRuntime({
    sendPasswordResetEmailCode: (payload) => {
      sendRequests.push(payload)
      return sendDeferred.promise
    },
    resetPassword: (payload) => {
      resetRequests.push(payload)
      return resetDeferred.promise
    }
  })
  runtime.form.email = 'driver@example.com'

  const firstSend = runtime.handleSendCode()
  await flushTasks()
  const duplicateSend = runtime.handleSendCode()
  await flushTasks()
  assert.equal(sendRequests.length, 1)
  sendDeferred.resolve()
  await Promise.all([firstSend, duplicateSend])

  runtime.form.verification_code = '123456'
  runtime.form.new_password = 'new-secret'
  runtime.form.confirm_password = 'new-secret'
  const firstReset = runtime.handleResetPassword()
  await flushTasks()
  const duplicateReset = runtime.handleResetPassword()
  await flushTasks()
  assert.deepEqual(resetRequests, [{
    email: 'driver@example.com',
    verification_code: '123456',
    new_password: 'new-secret'
  }])
  resetDeferred.resolve()
  await Promise.all([firstReset, duplicateReset])
  assert.deepEqual(runtime.navigations, ['/login'])
})


test('forgot password runtime clears secrets and timer when changing email', async () => {
  const runtime = createForgotPasswordRuntime()
  runtime.form.email = 'wrong@example.com'
  await runtime.handleSendCode()
  runtime.form.verification_code = '123456'
  runtime.form.new_password = 'new-secret'
  runtime.form.confirm_password = 'new-secret'

  runtime.handleChangeEmail()

  assert.equal(runtime.step.value, 'email')
  assert.equal(runtime.form.email, 'wrong@example.com')
  assert.equal(runtime.form.verification_code, '')
  assert.equal(runtime.form.new_password, '')
  assert.equal(runtime.form.confirm_password, '')
  assert.equal(runtime.countdown.value, 0)
  assert.equal(runtime.timers.active.size, 0)
})


test('forgot password runtime ignores a stale resend after changing email', async () => {
  const sendDeferred = createDeferred()
  const runtime = createForgotPasswordRuntime({
    sendPasswordResetEmailCode: () => sendDeferred.promise
  })
  runtime.form.email = 'old@example.com'
  runtime.step.value = 'reset'

  const resend = runtime.handleSendCode()
  await flushTasks()
  runtime.handleChangeEmail()
  runtime.form.email = 'new@example.com'
  sendDeferred.resolve()
  await resend

  assert.equal(runtime.step.value, 'email')
  assert.equal(runtime.form.email, 'new@example.com')
  assert.equal(runtime.sendLoading.value, false)
  assert.equal(runtime.countdown.value, 0)
  assert.equal(runtime.timers.active.size, 0)
  assert.deepEqual(runtime.notifications, [])
})


test('forgot password runtime does not restart work after unmount', async () => {
  const sendDeferred = createDeferred()
  const runtime = createForgotPasswordRuntime({
    sendPasswordResetEmailCode: () => sendDeferred.promise
  })
  runtime.form.email = 'driver@example.com'

  const sending = runtime.handleSendCode()
  await flushTasks()
  runtime.cleanup()
  sendDeferred.resolve()
  await sending

  assert.equal(runtime.step.value, 'email')
  assert.equal(runtime.countdown.value, 0)
  assert.equal(runtime.timers.active.size, 0)
  assert.deepEqual(runtime.notifications, [])
})


test('registration runtime starts countdown on success and includes the verification code', async () => {
  const sendRequests = []
  const registerRequests = []
  const runtime = createRegisterRuntime({
    sendRegisterEmailCode: async (payload) => sendRequests.push(payload),
    register: async (payload) => registerRequests.push(payload)
  })
  Object.assign(runtime.form, {
    username: 'driver',
    password: 'secret12',
    repassword: 'secret12',
    email: 'driver@example.com',
    verification_code: '654321'
  })

  await runtime.handleSendCode()
  await runtime.handleRegister()

  assert.deepEqual(sendRequests, [{ email: 'driver@example.com' }])
  assert.equal(runtime.countdown.value, 60)
  assert.equal(runtime.timers.active.size, 1)
  assert.deepEqual(registerRequests, [{
    username: 'driver',
    password: 'secret12',
    email: 'driver@example.com',
    verification_code: '654321'
  }])
  assert.deepEqual(runtime.navigations, ['/login'])

  runtime.cleanup()
  assert.equal(runtime.timers.active.size, 0)
})


test('registration runtime suppresses duplicate registration submits', async () => {
  const registerDeferred = createDeferred()
  const registerRequests = []
  const runtime = createRegisterRuntime({
    register: (payload) => {
      registerRequests.push(payload)
      return registerDeferred.promise
    }
  })
  Object.assign(runtime.form, {
    username: 'driver',
    password: 'secret12',
    repassword: 'secret12',
    email: 'driver@example.com',
    verification_code: '654321'
  })

  const firstSubmit = runtime.handleRegister()
  await flushTasks()
  const duplicateSubmit = runtime.handleRegister()
  await flushTasks()
  assert.equal(registerRequests.length, 1)

  registerDeferred.resolve()
  await Promise.all([firstSubmit, duplicateSubmit])
  assert.deepEqual(runtime.navigations, ['/login'])
})


test('registration runtime does not start countdown after a failed send', async () => {
  const runtime = createRegisterRuntime({
    sendRegisterEmailCode: async () => { throw new Error('network') }
  })
  runtime.form.email = 'driver@example.com'

  await runtime.handleSendCode()

  assert.equal(runtime.codeLoading.value, false)
  assert.equal(runtime.countdown.value, 0)
  assert.equal(runtime.timers.active.size, 0)
  assert.deepEqual(runtime.notifications, [])
})


test('registration runtime does not start a countdown after unmount', async () => {
  const sendDeferred = createDeferred()
  const runtime = createRegisterRuntime({
    sendRegisterEmailCode: () => sendDeferred.promise
  })
  runtime.form.email = 'driver@example.com'

  const sending = runtime.handleSendCode()
  await flushTasks()
  runtime.cleanup()
  sendDeferred.resolve()
  await sending

  assert.equal(runtime.countdown.value, 0)
  assert.equal(runtime.timers.active.size, 0)
  assert.deepEqual(runtime.notifications, [])
})
