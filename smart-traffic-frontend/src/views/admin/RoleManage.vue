<template>
  <div class="role-manage">
    <el-card>
      <template #header>
        <div class="header">
          <span>角色权限管理</span>
          <el-button type="primary" @click="showDialog = true">新增角色</el-button>
        </div>
      </template>

      <el-table :data="roles" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="角色名称" />
        <el-table-column prop="code" label="角色编码" />
        <el-table-column label="权限" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="p in row.permissions" :key="p" size="small" style="margin: 0 4px 4px 0">
              {{ p }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="editRole(row)">编辑</el-button>
            <el-popconfirm title="确定删除？" @confirm="deleteRole(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDialog" :title="form.id ? '编辑角色' : '新增角色'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="角色名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="角色编码">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="权限">
          <el-checkbox-group v-model="form.permissions">
            <el-checkbox label="case:review">案件审核</el-checkbox>
            <el-checkbox label="violation:manage">违章管理</el-checkbox>
            <el-checkbox label="stats:view">统计查看</el-checkbox>
            <el-checkbox label="user:manage">用户管理</el-checkbox>
            <el-checkbox label="system:config">系统配置</el-checkbox>
            <el-checkbox label="log:view">日志查看</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { getRoles, createRole, updateRole, deleteRole as apiDeleteRole } from '@/api/system'

const roles = ref([])
const showDialog = ref(false)
const form = reactive({ id: null, name: '', code: '', description: '', permissions: [] })

async function load() {
  const res = await getRoles()
  roles.value = res.data || []
}
load()

function editRole(row) {
  Object.assign(form, { ...row })
  showDialog.value = true
}

async function saveRole() {
  if (form.id) {
    await updateRole(form.id, form)
  } else {
    await createRole(form)
  }
  ElMessage.success('保存成功')
  showDialog.value = false
  load()
}

async function deleteRole(id) {
  await apiDeleteRole(id)
  ElMessage.success('删除成功')
  load()
}
</script>

<style scoped>
.role-manage { padding: 16px; }
.header { display: flex; justify-content: space-between; align-items: center; }
</style>
