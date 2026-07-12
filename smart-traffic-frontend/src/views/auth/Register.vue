<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-form-side">
        <div class="auth-brand">
          <div class="brand-label">智能交通违章管理平台</div>
          <h1 class="auth-title">用户注册</h1>
          <p class="auth-desc">创建您的账号，开启智能管理之旅</p>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" size="large">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
          </el-form-item>
          <el-form-item prop="repassword">
            <el-input v-model="form.repassword" type="password" placeholder="确认密码" prefix-icon="Lock" show-password />
          </el-form-item>
          <el-form-item prop="phone">
            <el-input v-model="form.phone" placeholder="手机号" prefix-icon="Phone" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" style="width:100%" @click="handleRegister">
              注 册
            </el-button>
          </el-form-item>
        </el-form>

        <div class="auth-footer">
          已有账号？<el-link type="primary" @click="router.push('/login')">立即登录</el-link>
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
import { register } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '', password: '', repassword: '', phone: ''
})

const validateRepassword = (rule, value, callback) => {
  if (value !== form.password) callback(new Error('两次密码不一致'))
  else callback()
}

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码不少于6位', trigger: 'blur' }],
  repassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateRepassword, trigger: 'blur' }
  ],
  phone: [{ required: true, pattern: /^1\d{10}$/, message: '请输入正确的手机号', trigger: 'blur' }]
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await register({ username: form.username, password: form.password, phone: form.phone })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (err) {
    ElMessage.error(err.response?.data?.message || '注册失败')
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

:deep(.el-select .el-input__wrapper) {
  border-radius: 12px !important;
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

:deep(.el-link) {
  font-weight: 500;
  font-size: 13px;
}

.auth-form-side {
  overflow-y: auto;
  max-height: 100vh;
}
</style>
