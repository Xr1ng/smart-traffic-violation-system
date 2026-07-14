<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-form-side">
        <div class="auth-brand">
          <div class="brand-label">智能交通违章管理平台</div>
          <h1 class="auth-title">用户登录</h1>
          <p class="auth-desc">AI 驱动的交通违章智能管理系统</p>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" size="large">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <div class="auth-extra">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <el-link type="primary" :underline="false" style="font-size:13px" @click="openReset">忘记密码？</el-link>
          </div>
          <el-form-item>
            <el-button type="primary" :loading="loading" style="width:100%" @click="handleLogin">
              登 录
            </el-button>
          </el-form-item>
        </el-form>

        <div class="auth-footer">
          还没有账号？<el-link type="primary" @click="router.push('/register')">立即注册</el-link>
        </div>
      </div>

      <div class="auth-visual-side">
        <img src="/images/auth-bg.png" alt="Smart Traffic" />
      </div>
    </div>

    <!-- 忘记密码对话框 -->
    <el-dialog v-model="resetVisible" title="重置密码" width="420px" :close-on-click-modal="false" center>
      <!-- 步骤1：验证身份 -->
      <el-form v-if="resetStep === 1" ref="resetForm1Ref" :model="resetForm" :rules="resetRules1" size="large" @keyup.enter="handleSendCode">
        <el-form-item prop="username">
          <el-input v-model="resetForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item prop="email">
          <el-input v-model="resetForm.email" placeholder="请输入注册邮箱" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="sendLoading" style="width:100%" @click="handleSendCode">
            {{ sendLoading ? '验证中...' : '获取验证码' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 步骤2：重置密码 -->
      <el-form v-else ref="resetForm2Ref" :model="resetForm" :rules="resetRules2" size="large" @keyup.enter="handleReset">
        <el-form-item prop="code">
          <div style="display:flex;gap:10px;width:100%">
            <el-input v-model="resetForm.code" placeholder="请输入验证码" style="flex:1" />
            <el-button
              :disabled="resetCountdown > 0"
              style="width:120px;flex-shrink:0"
              @click="handleSendCode"
            >
              {{ resetCountdown > 0 ? `${resetCountdown}s 后重发` : '重新获取' }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item prop="new_password">
          <el-input v-model="resetForm.new_password" type="password" placeholder="请输入新密码" show-password />
        </el-form-item>
        <el-form-item prop="repassword">
          <el-input v-model="resetForm.repassword" type="password" placeholder="请确认新密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="resetLoading" style="width:100%" @click="handleReset">
            {{ resetLoading ? '重置中...' : '重置密码' }}
          </el-button>
        </el-form-item>
        <div style="text-align:center">
          <el-link type="primary" :underline="false" style="font-size:13px" @click="resetStep = 1">返回上一步</el-link>
        </div>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { forgotPasswordVerify, forgotPasswordReset } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// ========== 忘记密码 ==========
const resetVisible = ref(false)
const resetStep = ref(1)
const sendLoading = ref(false)
const resetLoading = ref(false)
const resetCountdown = ref(0)
const resetForm1Ref = ref(null)
const resetForm2Ref = ref(null)

const resetForm = reactive({
  username: '',
  email: '',
  code: '',
  new_password: '',
  repassword: ''
})

const resetRules1 = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const validateRePassword = (rule, value, callback) => {
  if (value !== resetForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const resetRules2 = {
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  repassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateRePassword, trigger: 'blur' }
  ]
}

function openReset() {
  resetStep.value = 1
  resetForm.username = form.username || ''
  resetForm.email = ''
  resetForm.code = ''
  resetForm.new_password = ''
  resetForm.repassword = ''
  resetVisible.value = true
}

function startResetCountdown() {
  resetCountdown.value = 60
  const timer = setInterval(() => {
    resetCountdown.value--
    if (resetCountdown.value <= 0) clearInterval(timer)
  }, 1000)
}

async function handleSendCode() {
  const valid = await resetForm1Ref.value.validate().catch(() => false)
  if (!valid) return

  sendLoading.value = true
  try {
    await forgotPasswordVerify({ username: resetForm.username, email: resetForm.email })
    ElMessage.success('验证码已发送至您的邮箱，请注意查收')
    resetStep.value = 2
    resetForm.code = ''
    startResetCountdown()
  } catch (e) {
    // 后端会返回错误信息
  } finally {
    sendLoading.value = false
  }
}

async function handleReset() {
  const valid = await resetForm2Ref.value.validate().catch(() => false)
  if (!valid) return

  resetLoading.value = true
  try {
    await forgotPasswordReset({
      username: resetForm.username,
      email: resetForm.email,
      code: resetForm.code,
      new_password: resetForm.new_password
    })
    ElMessage.success('密码重置成功，请重新登录')
    resetVisible.value = false
    form.username = resetForm.username
    form.password = ''
  } finally {
    resetLoading.value = false
  }
}

// ========== 登录 ==========
async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login({ username: form.username, password: form.password })
    if (rememberMe.value) {
      localStorage.setItem('remember_username', form.username)
    } else {
      localStorage.removeItem('remember_username')
    }
    ElMessage.success('登录成功')
    router.push(userStore.homePath)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
:deep(.el-input__wrapper) {
  border-radius: 12px !important;
  box-shadow: none !important;
  background: #FEFDF8 !important;
  padding: 4px 16px !important;
  border: 1px solid transparent !important;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #A2D9F0 !important;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #72a8c4 !important;
  box-shadow: 0 0 0 3px rgba(114, 168, 196, 0.15) !important;
}

:deep(.el-input__inner) {
  height: 46px;
  font-size: 14px;
  color: #2c3e50;
  background: transparent !important;
}

:deep(.el-input__inner::placeholder) {
  color: #919CA3;
}

:deep(.el-button--primary) {
  border-radius: 12px !important;
  height: 48px;
  font-size: 15px;
  font-weight: 600;
  background: linear-gradient(135deg, #72a8c4 0%, #5b93af 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(114, 168, 196, 0.35) !important;
  transition: all 0.3s ease;
}

:deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(114, 168, 196, 0.45) !important;
}

:deep(.el-checkbox__label) {
  font-size: 13px;
  color: #919CA3;
}

:deep(.el-link) {
  font-weight: 500;
  font-size: 13px;
}

.auth-extra a {
  color: #72a8c4;
  cursor: pointer;
  transition: color 0.2s;
}

.auth-extra a:hover {
  color: #5b93af;
  text-decoration: underline;
}
</style>
