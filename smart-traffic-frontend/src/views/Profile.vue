<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">个人信息</h2>
    </div>

    <el-card style="max-width:600px" v-loading="loading">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" disabled />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="角色">
          <el-tag>{{ roleName }}</el-tag>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSave">保存修改</el-button>
          <el-button @click="showPasswordDialog = true">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 修改密码弹窗 -->
    <el-dialog title="修改密码" v-model="showPasswordDialog" width="400px">
      <el-form :model="pwdForm" label-width="90px">
        <el-form-item label="旧密码">
          <el-input v-model="pwdForm.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="pwdForm.rePassword" type="password" show-password />
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
import { ElMessage } from 'element-plus'
import { getUserInfo, updateProfile, changePassword } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const loading = ref(false)
const submitting = ref(false)
const showPasswordDialog = ref(false)
const formRef = ref(null)

const form = reactive({ username: '', phone: '' })
const pwdForm = reactive({ oldPassword: '', newPassword: '', rePassword: '' })

const rules = {
  phone: [{ required: true, pattern: /^1\d{10}$/, message: '请输入正确手机号', trigger: 'blur' }]
}

const roleName = computed(() => {
  const map = { admin: '超级管理员', reviewer: '审核员', citizen: '市民' }
  return map[userStore.role] || '未知'
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
    await updateProfile({ phone: form.phone })
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

onMounted(fetchProfile)
</script>
