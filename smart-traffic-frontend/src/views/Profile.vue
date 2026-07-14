<template>
  <div class="profile-page" v-loading="loading">
    <section class="identity-band">
      <el-avatar :size="88" :src="avatarUrl" class="role-avatar">
        {{ form.username?.slice(0, 1)?.toUpperCase() }}
      </el-avatar>
      <div class="identity-copy">
        <div class="identity-heading">
          <h2>{{ form.username || '个人资料' }}</h2>
          <el-tag :type="roleTagType" effect="dark">{{ roleName }}</el-tag>
        </div>
        <p>{{ form.email || '尚未设置邮箱' }}</p>
      </div>
    </section>

    <div class="profile-grid">
      <el-card shadow="never" class="profile-panel">
        <template #header>
          <div class="panel-title">
            <el-icon><User /></el-icon>
            <span>基本信息</span>
          </div>
        </template>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
          <el-form-item label="用户名">
            <el-input v-model="form.username" disabled />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入手机号" clearable />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="请输入邮箱" clearable />
          </el-form-item>
          <div class="form-actions">
            <el-button type="primary" :loading="submitting" @click="handleSave">
              保存修改
            </el-button>
          </div>
        </el-form>
      </el-card>

      <el-card shadow="never" class="profile-panel security-panel">
        <template #header>
          <div class="panel-title">
            <el-icon><Lock /></el-icon>
            <span>账号安全</span>
          </div>
        </template>

        <div class="security-row">
          <div>
            <strong>登录密码</strong>
            <p>修改后需要使用新密码重新登录。</p>
          </div>
          <el-button @click="openPasswordDialog">修改密码</el-button>
        </div>
      </el-card>
    </div>

    <el-dialog
      v-model="showPasswordDialog"
      title="修改密码"
      width="min(420px, calc(100vw - 32px))"
      :close-on-click-modal="false"
      @closed="resetPasswordForm"
    >
      <el-form :model="pwdForm" label-position="top">
        <el-form-item label="旧密码">
          <el-input v-model="pwdForm.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="pwdForm.rePassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" :loading="passwordSubmitting" @click="handleChangePwd">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { changePassword, getUserInfo, updateProfile } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const submitting = ref(false)
const passwordSubmitting = ref(false)
const showPasswordDialog = ref(false)
const formRef = ref(null)

const form = reactive({ username: '', phone: '', email: '' })
const pwdForm = reactive({ oldPassword: '', newPassword: '', rePassword: '' })

const rules = {
  phone: [{ pattern: /^$|^1\d{10}$/, message: '请输入正确手机号', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const roleName = computed(() => ({
  admin: '超级管理员',
  reviewer: '审核员',
  citizen: '市民'
}[userStore.role] || '未知角色'))

const roleTagType = computed(() => ({
  admin: 'danger',
  reviewer: 'warning',
  citizen: 'success'
}[userStore.role] || 'info'))

const avatarUrl = computed(() => ({
  admin: '/images/admin.jpg',
  reviewer: '/images/reviewer.jpg',
  citizen: '/images/citizen.jpg'
}[userStore.role] || ''))

async function fetchProfile() {
  loading.value = true
  try {
    const response = await getUserInfo()
    Object.assign(form, response.data)
    userStore.setUserInfo(response.data)
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid || submitting.value) return
  submitting.value = true
  try {
    const response = await updateProfile({ phone: form.phone, email: form.email })
    userStore.setUserInfo(response.data)
    Object.assign(form, response.data)
    ElMessage.success('保存成功')
  } finally {
    submitting.value = false
  }
}

function openPasswordDialog() {
  resetPasswordForm()
  showPasswordDialog.value = true
}

function resetPasswordForm() {
  Object.assign(pwdForm, { oldPassword: '', newPassword: '', rePassword: '' })
}

async function handleChangePwd() {
  if (!pwdForm.oldPassword || !pwdForm.newPassword || !pwdForm.rePassword) {
    return ElMessage.warning('请填写完整')
  }
  if (pwdForm.newPassword !== pwdForm.rePassword) {
    return ElMessage.warning('两次密码不一致')
  }
  if (passwordSubmitting.value) return

  passwordSubmitting.value = true
  try {
    await changePassword({
      old_password: pwdForm.oldPassword,
      new_password: pwdForm.newPassword
    })
    ElMessage.success('密码修改成功，请重新登录')
    showPasswordDialog.value = false
    userStore.logout()
    router.push('/login')
  } finally {
    passwordSubmitting.value = false
  }
}

onMounted(fetchProfile)
</script>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1040px;
  margin: 0 auto;
}

.identity-band {
  display: flex;
  align-items: center;
  gap: 20px;
  min-height: 150px;
  padding: 24px 28px;
  color: #fff;
  background: #294d5c;
  border-left: 6px solid #e6a23c;
  border-radius: 8px;
}

.role-avatar {
  flex: 0 0 auto;
  border: 3px solid rgba(255, 255, 255, 0.8);
  background: #dfe7eb;
}

.identity-copy {
  min-width: 0;
}

.identity-heading {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.identity-heading h2 {
  margin: 0;
  font-size: 24px;
  letter-spacing: 0;
}

.identity-copy p {
  margin: 8px 0 0;
  color: rgba(255, 255, 255, 0.78);
  overflow-wrap: anywhere;
}

.profile-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(280px, 1fr);
  gap: 20px;
}

.profile-panel {
  border-radius: 8px;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.security-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.security-row strong {
  color: var(--text-color);
}

.security-row p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

@media (max-width: 760px) {
  .identity-band {
    align-items: flex-start;
    padding: 20px;
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }

  .security-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
