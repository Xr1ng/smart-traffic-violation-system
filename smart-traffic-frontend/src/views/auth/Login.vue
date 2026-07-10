<template>
  <div class="login-wrapper">
    <div class="login-card">
      <h2>智能交通违章管理平台</h2>
      <p class="subtitle">AI 驱动的交通违章智能管理系统</p>

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
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width:100%" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="footer-link">
        还没有账号？<el-link type="primary" @click="router.push('/register')">立即注册</el-link>
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
    ElMessage.success('登录成功')
    router.push(userStore.homePath)
  } finally {
    loading.value = false
  }
}
</script>
