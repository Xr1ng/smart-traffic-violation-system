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
            <el-input v-model="form.username" placeholder="请输入真实姓名" prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
          </el-form-item>
          <el-form-item prop="repassword">
            <el-input v-model="form.repassword" type="password" placeholder="确认密码" prefix-icon="Lock" show-password />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item prop="verification_code">
            <div style="display:flex; gap:12px; width:100%">
              <el-input v-model="form.verification_code" placeholder="请输入验证码" style="flex:1" />
              <el-button
                type="primary"
                :disabled="countdown > 0 || !form.email"
                style="width:120px"
                @click="handleSendCode"
              >
                {{ countdown > 0 ? `${countdown}s 后重发` : '获取验证码' }}
              </el-button>
            </div>
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
import { register, registerSendCode } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const countdown = ref(0)

const form = reactive({
  username: '', password: '', repassword: '', email: '', verification_code: ''
})

const validateRepassword = (rule, value, callback) => {
  if (value !== form.password) callback(new Error('两次密码不一致'))
  else callback()
}

const rules = {
  username: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码不少于6位', trigger: 'blur' }],
  repassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateRepassword, trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  verification_code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' }
  ]
}

async function handleSendCode() {
  try {
    await registerSendCode({ email: form.email })
    ElMessage.success('验证码已发送至您的邮箱，请注意查收')
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '验证码发送失败')
  }
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await register({
      username: form.username,
      password: form.password,
      email: form.email,
      verification_code: form.verification_code
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
::v-deep(.el-input__wrapper) {
  border-radius: 12px !important;
  box-shadow: none !important;
  background: #FEFDF8 !important;
  padding: 4px 16px !important;
  border: 1px solid transparent !important;
  transition: all 0.3s ease;
}

::v-deep(.el-input__wrapper:hover) {
  border-color: #A2D9F0 !important;
}

::v-deep(.el-input__wrapper.is-focus) {
  border-color: #72a8c4 !important;
  box-shadow: 0 0 0 3px rgba(114, 168, 196, 0.15) !important;
}

::v-deep(.el-input__inner) {
  height: 46px;
  font-size: 14px;
  color: #2c3e50;
  background: transparent !important;
}

::v-deep(.el-input__inner::placeholder) {
  color: #919CA3;
}

::v-deep(.el-select .el-input__wrapper) {
  border-radius: 12px !important;
}

::v-deep(.el-button--primary) {
  border-radius: 12px !important;
  height: 48px;
  font-size: 15px;
  font-weight: 600;
  background: linear-gradient(135deg, #72a8c4 0%, #5b93af 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(114, 168, 196, 0.35) !important;
  transition: all 0.3s ease;
}

::v-deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(114, 168, 196, 0.45) !important;
}

::v-deep(.el-link) {
  font-weight: 500;
  font-size: 13px;
}

.auth-form-side {
  overflow-y: auto;
  max-height: 100vh;
}
</style>
