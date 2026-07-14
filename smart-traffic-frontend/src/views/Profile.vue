<template>
  <div class="profile-page">
    <!-- 顶部蓝色横幅 -->
    <div class="profile-banner">
      <div class="banner-content">
        <el-avatar :size="80" :src="avatarUrl" class="avatar">
          <span class="avatar-text">{{ form.username ? form.username.charAt(0).toUpperCase() : '?' }}</span>
        </el-avatar>
        <div class="banner-info">
          <h2 class="user-name">{{ form.username }}</h2>
          <p class="user-role">{{ roleName }}</p>
        </div>
      </div>
    </div>

    <!-- 表单卡片 -->
    <div class="profile-body">
      <div class="profile-grid">
        <el-card class="profile-card" v-loading="loading">
          <template #header>
            <div class="card-title">
              <el-icon><User /></el-icon>
              <span>账户信息</span>
            </div>
          </template>
          <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" size="large">
            <el-form-item label="用户名">
              <el-input v-model="form.username" disabled />
            </el-form-item>
            <el-form-item v-if="isCitizen" label="邮箱" prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="角色">
              <el-tag :type="roleTagType" size="large">{{ roleName }}</el-tag>
            </el-form-item>
            <el-form-item v-if="isCitizen">
              <el-button type="primary" :loading="submitting" @click="handleSave">保存修改</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="profile-card">
          <template #header>
            <div class="card-title">
              <el-icon><Setting /></el-icon>
              <span>安全中心</span>
            </div>
          </template>
          <div class="security-list">
            <div class="security-item" @click="showPasswordDialog = true">
              <div class="sec-icon lock-bg">
                <el-icon><Lock /></el-icon>
              </div>
              <div class="sec-info">
                <div class="sec-title">修改密码</div>
                <div class="sec-desc">定期更换密码可提升账户安全性</div>
              </div>
              <el-icon class="sec-arrow"><ArrowRight /></el-icon>
            </div>
            <div class="security-item">
              <div class="sec-icon theme-bg">
                <el-icon><Moon /></el-icon>
              </div>
              <div class="sec-info">
                <div class="sec-title">深色模式</div>
                <div class="sec-desc">切换系统明暗主题</div>
              </div>
              <el-switch v-model="themeStore.isDark" size="small" />
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 修改密码弹窗 -->
    <el-dialog title="修改密码" v-model="showPasswordDialog" width="420px">
      <el-form :model="pwdForm" label-width="90px">
        <el-form-item label="旧密码">
          <el-input v-model="pwdForm.oldPassword" type="password" show-password placeholder="请输入旧密码" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.newPassword" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="pwdForm.rePassword" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="handleChangePwd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserInfo, updateProfile, changePassword } from '@/api/auth'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { useRouter } from 'vue-router'
import { User, Setting, Lock, Moon, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const themeStore = useThemeStore()
const loading = ref(false)
const submitting = ref(false)
const showPasswordDialog = ref(false)
const formRef = ref(null)

const form = reactive({ username: '', email: '' })
const pwdForm = reactive({ oldPassword: '', newPassword: '', rePassword: '' })

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const roleName = computed(() => {
  const map = { admin: '超级管理员', reviewer: '审核员', citizen: '市民' }
  return map[userStore.role] || '未知'
})

const isCitizen = computed(() => userStore.role === 'citizen')

const avatarUrl = computed(() => {
  const map = { admin: '/images/admin.jpg', reviewer: '/images/reviewer.jpg', citizen: '/images/citizen.jpg' }
  return map[userStore.role] || ''
})

const roleTagType = computed(() => {
  const map = { admin: 'danger', reviewer: 'primary', citizen: 'success' }
  return map[userStore.role] || 'info'
})

async function fetchProfile() {
  loading.value = true
  try {
    const res = await getUserInfo()
    Object.assign(form, res.data)
  } catch { /* handled */ }
  finally { loading.value = false }
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await updateProfile({ email: form.email })
    ElMessage.success('保存成功')
  } catch { /* handled */ }
  finally { submitting.value = false }
}

async function handleChangePwd() {
  if (!pwdForm.oldPassword || !pwdForm.newPassword) {
    return ElMessage.warning('请填写完整')
  }
  if (pwdForm.newPassword !== pwdForm.rePassword) {
    return ElMessage.warning('两次密码不一致')
  }
  try {
    await changePassword({ old_password: pwdForm.oldPassword, new_password: pwdForm.newPassword })
    ElMessage.success('密码修改成功，请重新登录')
    showPasswordDialog.value = false
    userStore.logout()
  } catch { /* handled */ }
}

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' }).then(() => {
    userStore.logout()
    router.push('/login')
  })
}

onMounted(fetchProfile)
</script>

<style scoped>
.profile-page {
  min-height: 100%;
  background: linear-gradient(135deg, #EBF3F7 0%, #eef6f9 50%, #EBF3F7 100%);
  position: relative;
  overflow: hidden;
}

.profile-page::before {
  content: '';
  position: absolute;
  top: -120px;
  right: -120px;
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(162, 217, 240, 0.15) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.profile-page::after {
  content: '';
  position: absolute;
  bottom: -80px;
  left: -80px;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(58, 90, 104, 0.06) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

/* 顶部横幅 */
.profile-banner {
  position: relative;
  z-index: 1;
  margin-bottom: 24px;
  padding: 36px 40px;
  background: linear-gradient(135deg, #3A5A68 0%, #4B6E7D 50%, #3A5A68 100%);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(58, 90, 104, 0.3);
  overflow: hidden;
}

.profile-banner::before {
  content: '';
  position: absolute;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
  top: -40px;
  right: 8%;
}

.profile-banner::after {
  content: '';
  position: absolute;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: rgba(255,255,255,0.04);
  bottom: -30px;
  right: 25%;
}

.banner-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar {
  background: #e8edf2;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  font-size: 32px;
  font-weight: bold;
  border: 3px solid rgba(255,255,255,0.6);
}

.avatar img {
  object-fit: cover;
}

.avatar-text {
  color: #919CA3;
}

.banner-info {
  color: #fff;
}

.user-name {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 4px 0;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.user-role {
  font-size: 14px;
  color: rgba(255,255,255,0.85);
  margin: 0;
}

/* 卡片区域 */
.profile-body {
  position: relative;
  z-index: 1;
}

.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 900px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}

.profile-card {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.04);
  transition: box-shadow 0.3s;
}

.profile-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.04);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.card-title .el-icon {
  font-size: 18px;
  color: #72a8c4;
}

/* 安全中心列表 */
.security-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.security-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s;
  border: 1px solid transparent;
}

.security-item:hover {
  background: #f8faf9;
  border-color: #d0d9de;
}

.sec-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sec-icon .el-icon {
  font-size: 20px;
}

.lock-bg {
  background: #e5f4fa;
  color: #72a8c4;
}

.theme-bg {
  background: #eff0f1;
  color: #919CA3;
}

.sec-info {
  flex: 1;
}

.sec-title {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 2px;
}

.sec-desc {
  font-size: 12px;
  color: #919CA3;
}

.sec-arrow {
  color: #bcc5ca;
  font-size: 14px;
}
</style>
