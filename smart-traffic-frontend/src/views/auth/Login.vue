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
            <a @click="router.push('/register')">忘记密码？</a>
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
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'

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

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await login({ username: form.username, password: form.password })
    const { access_token, user } = res.data
    userStore.token = access_token
    userStore.role = user.role_code
    userStore.userInfo = { id: user.id, username: user.username, role: user.role_code }
    localStorage.setItem('token', access_token)
    localStorage.setItem('role', user.role_code)
    localStorage.setItem('userInfo', JSON.stringify({ id: user.id, username: user.username, role: user.role_code }))
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
  background: transparent !important;
}

:deep(.el-input__inner::placeholder) {
  color: #a0aec0;
}

:deep(.el-button--primary) {
  border-radius: 12px !important;
  height: 48px;
  font-size: 15px;
  font-weight: 600;
  background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(74, 144, 226, 0.3) !important;
  transition: all 0.3s ease;
}

:deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(74, 144, 226, 0.4) !important;
}

:deep(.el-checkbox__label) {
  font-size: 13px;
  color: #8898aa;
}

:deep(.el-link) {
  font-weight: 500;
  font-size: 13px;
}

.auth-extra a {
  color: #4a90e2;
  cursor: pointer;
  transition: color 0.2s;
}

.auth-extra a:hover {
  color: #357abd;
  text-decoration: underline;
}
</style>
