<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <el-button type="primary" @click="openCreate">新增用户</el-button>
    </div>

    <el-card>
      <el-table :data="users" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role_code === 'admin' ? 'danger' : row.role_code === 'reviewer' ? 'warning' : 'info'" size="small">
              {{ roleMap[row.role_code] || row.role_code }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.status" active-value="active" inactive-value="disabled" @change="newStatus => toggleStatus(row, newStatus)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" @click="editUser(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑用户' : '新增用户'" width="500px">
      <el-form ref="formRef" :model="dialog.form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="dialog.form.username" :disabled="dialog.isEdit" />
        </el-form-item>
        <el-form-item v-if="!dialog.isEdit" label="密码" prop="password">
          <el-input v-model="dialog.form.password" type="password" show-password />
        </el-form-item>
        <el-form-item v-if="!dialog.isEdit" label="手机号">
          <el-input v-model="dialog.form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="dialog.form.email" />
        </el-form-item>
        <el-form-item label="角色" prop="role_code">
          <el-select v-model="dialog.form.role_code" style="width:100%">
            <el-option label="市民" value="citizen" />
            <el-option label="审核员" value="reviewer" />
            <el-option label="超级管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, onMounted } from 'vue'
import { fetchUsers, createUser, updateUser } from '@/api/system'
import { ElMessage } from 'element-plus'
import {
  buildUserCreatePayload,
  buildUserUpdatePayload,
  persistUserStatus
} from '@/utils/contracts'

const roleMap = { citizen: '市民', reviewer: '审核员', admin: '管理员' }
const users = ref([])
const formRef = ref(null)
const submitting = ref(false)

function emptyForm() {
  return {
    id: null,
    username: '',
    password: '',
    phone: '',
    email: '',
    role_code: 'citizen',
    status: 'active'
  }
}

const dialog = ref({
  visible: false,
  isEdit: false,
  form: emptyForm()
})

const rules = computed(() => ({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  role_code: [{ required: true, message: '请选择角色', trigger: 'change' }],
  ...(dialog.value.isEdit
    ? {}
    : { password: [{ required: true, message: '请输入密码', trigger: 'blur' }] })
}))

async function loadUsers() {
  try {
    const res = await fetchUsers({ page: 1, page_size: 100 })
    users.value = res.data.items
  } catch { /* handled by interceptor */ }
}

function openCreate() {
  dialog.value = { visible: true, isEdit: false, form: emptyForm() }
  nextTick(() => formRef.value?.clearValidate())
}

function editUser(row) {
  dialog.value = {
    visible: true,
    isEdit: true,
    form: {
      id: row.id,
      username: row.username,
      password: '',
      phone: row.phone ?? '',
      email: row.email ?? '',
      role_code: row.role_code,
      status: row.status
    }
  }
  nextTick(() => formRef.value?.clearValidate())
}

async function saveUser() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  const f = dialog.value.form
  submitting.value = true
  try {
    if (dialog.value.isEdit) {
      await updateUser(f.id, buildUserUpdatePayload(f))
    } else {
      await createUser(buildUserCreatePayload(f))
    }
    dialog.value.visible = false
    ElMessage.success('保存成功')
    loadUsers()
  } catch { /* handled by interceptor */ }
  finally {
    submitting.value = false
  }
}

async function toggleStatus(row, newStatus) {
  await persistUserStatus(row, newStatus, updateUser)
}

onMounted(loadUsers)
</script>

<style scoped>
.page-container { }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { font-size: 20px; margin: 0; }
</style>
