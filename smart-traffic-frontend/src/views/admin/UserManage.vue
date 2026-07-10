<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <el-button type="primary" @click="dialog.visible = true">新增用户</el-button>
    </div>

    <el-card>
      <el-table :data="users" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'reviewer' ? 'warning' : 'info'" size="small">
              {{ roleMap[row.role] || row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.status" active-value="enabled" inactive-value="disabled" @change="toggleStatus(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="editUser(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑用户' : '新增用户'" width="500px">
      <el-form :model="dialog.form" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="dialog.form.username" :disabled="dialog.isEdit" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="dialog.form.phone" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="dialog.form.role" style="width:100%">
            <el-option label="市民" value="citizen" />
            <el-option label="审核员" value="reviewer" />
            <el-option label="超级管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchUsers, createUser, updateUser } from '@/api/system'
import { ElMessage, ElMessageBox } from 'element-plus'

const roleMap = { citizen: '市民', reviewer: '审核员', admin: '管理员' }
const users = ref([])

const dialog = ref({
  visible: false,
  isEdit: false,
  form: { username: '', phone: '', email: '', role_code: 'citizen' }
})

async function loadUsers() {
  const res = await fetchUsers({ page: 1, page_size: 100 })
  users.value = res.data.items
}

function editUser(row) {
  dialog.value = { visible: true, isEdit: true, form: { ...row } }
}

async function deleteUser(row) {
  ElMessageBox.confirm('确定删除？', '确认', { type: 'warning' }).then(async () => {
    await updateUser(row.id, { status: 'disabled' })
    loadUsers(); ElMessage.success('已禁用')
  })
}

async function saveUser() {
  const f = dialog.value.form
  if (dialog.value.isEdit) {
    await updateUser(f.id, { phone: f.phone, email: f.email, role_code: f.role_code })
  } else {
    await createUser({ username: f.username, phone: f.phone, email: f.email, role_code: f.role_code })
  }
  dialog.value.visible = false; loadUsers(); ElMessage.success('保存成功')
}

async function toggleStatus(row) {
  const newStatus = row.status === 'active' ? 'disabled' : 'active'
  await updateUser(row.id, { status: newStatus }); loadUsers()
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
