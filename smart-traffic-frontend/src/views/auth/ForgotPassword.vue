<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-form-side forgot-form-side">
        <div class="auth-brand">
          <div class="brand-label">智能交通违章管理平台</div>
          <h1 class="auth-title">{{ step === 'email' ? '找回密码' : '设置新密码' }}</h1>
          <p class="auth-desc">
            {{ step === 'email' ? '通过注册邮箱验证身份' : '输入邮件中的验证码并设置新密码' }}
          </p>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" size="large">
          <el-form-item prop="email">
            <el-input
              v-model="form.email"
              placeholder="请输入注册邮箱"
              prefix-icon="Message"
              :readonly="step === 'reset'"
            />
          </el-form-item>

          <div v-if="step === 'reset'" class="change-email-row">
            <el-button link type="primary" @click="handleChangeEmail">更换邮箱</el-button>
          </div>

          <template v-if="step === 'reset'">
            <el-form-item prop="verification_code">
              <div class="code-row">
                <el-input
                  v-model="form.verification_code"
                  placeholder="请输入验证码"
                  prefix-icon="Key"
                  maxlength="6"
                />
                <el-button
                  :loading="sendLoading"
                  :disabled="countdown > 0 || sendLoading"
                  @click="handleSendCode"
                >
                  {{ countdown > 0 ? `${countdown}s` : '重新发送' }}
                </el-button>
              </div>
            </el-form-item>
            <el-form-item prop="new_password">
              <el-input
                v-model="form.new_password"
                type="password"
                placeholder="请输入新密码"
                prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item prop="confirm_password">
              <el-input
                v-model="form.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                prefix-icon="Lock"
                show-password
                @keyup.enter="handleResetPassword"
              />
            </el-form-item>
          </template>

          <el-form-item>
            <el-button
              v-if="step === 'email'"
              type="primary"
              :loading="sendLoading"
              class="submit-button"
              @click="handleSendCode"
            >
              发送验证码
            </el-button>
            <el-button
              v-else
              type="primary"
              :loading="resetLoading"
              class="submit-button"
              @click="handleResetPassword"
            >
              确认重置
            </el-button>
          </el-form-item>
        </el-form>

        <div class="auth-footer">
          想起密码了？<el-link type="primary" @click="router.push('/login')">返回登录</el-link>
        </div>
      </div>

      <div class="auth-visual-side">
        <img src="/images/auth-bg.png" alt="Smart Traffic" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { resetPassword, sendPasswordResetEmailCode } from '@/api/auth'

const router = useRouter()
const formRef = ref(null)
const step = ref('email')
const sendLoading = ref(false)
const resetLoading = ref(false)
const countdown = ref(0)
let countdownTimer = null

const form = reactive({
  email: '',
  verification_code: '',
  new_password: '',
  confirm_password: ''
})

const validatePasswordConfirmation = (_rule, value, callback) => {
  if (value !== form.new_password) callback(new Error('两次密码不一致'))
  else callback()
}

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  verification_code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码为6位数字', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码不少于6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validatePasswordConfirmation, trigger: 'blur' }
  ]
}

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

function handleChangeEmail() {
  stopCountdown()
  countdown.value = 0
  form.verification_code = ''
  form.new_password = ''
  form.confirm_password = ''
  step.value = 'email'
}

async function handleSendCode() {
  const valid = await formRef.value.validateField('email')
    .then(() => true)
    .catch(() => false)
  if (!valid || sendLoading.value || countdown.value > 0) return

  sendLoading.value = true
  try {
    await sendPasswordResetEmailCode({ email: form.email })
    step.value = 'reset'
    ElMessage.success('如果邮箱可用，验证码将发送至该邮箱')
    startCountdown()
  } catch (_) {
    // 请求拦截器统一显示后端错误信息。
  } finally {
    sendLoading.value = false
  }
}

async function handleResetPassword() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid || resetLoading.value) return

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
    // 请求拦截器统一显示后端错误信息。
  } finally {
    resetLoading.value = false
  }
}
</script>

<style scoped>
:deep(.el-input__wrapper) {
  border-radius: 12px !important;
  box-shadow: none !important;
  background: #f5f7fa !important;
  padding: 4px 16px !important;
  border: 1px solid transparent !important;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #d0d7de !important;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #4a90e2 !important;
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1) !important;
}

:deep(.el-input__inner) {
  height: 46px;
  font-size: 14px;
  color: #2d3748;
}

:deep(.el-button--primary) {
  border: none !important;
  background: #357abd !important;
}

.forgot-form-side {
  min-height: 590px;
}

.code-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 124px;
  gap: 12px;
  width: 100%;
}

.code-row .el-button {
  height: 48px;
}

.change-email-row {
  display: flex;
  justify-content: flex-end;
  margin: -14px 0 8px;
}

.submit-button {
  width: 100%;
  height: 48px;
  font-weight: 600;
}

@media (max-width: 420px) {
  .code-row {
    grid-template-columns: minmax(0, 1fr) 108px;
    gap: 8px;
  }
}
</style>
