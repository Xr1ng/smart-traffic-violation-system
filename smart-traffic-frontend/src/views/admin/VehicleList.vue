<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">车辆管理</h2>
      <el-button type="primary" @click="openDialog()">新 增 车 辆</el-button>
    </div>

    <!-- 搜索栏 -->
    <div class="table-toolbar">
      <div class="left">
        <el-input v-model="search.plate" placeholder="车牌号" clearable style="width:180px" @change="fetchList" />
        <el-button type="primary" @click="fetchList">查询</el-button>
        <el-button @click="resetSearch">重置</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <el-table :data="listWithOwner" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="plate_no" label="车牌号" width="130" />
      <el-table-column prop="owner_name" label="车主姓名" width="120" />
      <el-table-column prop="vehicle_type" label="车辆类型" min-width="140" />
      <el-table-column prop="color" label="颜色" width="100" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div style="display:flex;justify-content:flex-end;margin-top:16px">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @change="fetchList"
      />
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog :title="dialogTitle" v-model="dialogVisible" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="车牌号" prop="plate_no">
          <el-input v-model="form.plate_no" />
        </el-form-item>
        <el-form-item label="用户姓名" prop="owner_id">
          <el-select
            v-model="form.owner_id"
            placeholder="请选择用户"
            filterable
            clearable
            style="width:100%"
          >
            <el-option
              v-for="u in userList"
              :key="u.id"
              :label="u.username"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="车辆类型" prop="vehicle_type">
          <el-input v-model="form.vehicle_type" />
        </el-form-item>
        <el-form-item label="颜色" prop="color">
          <el-input v-model="form.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getVehicles, createVehicle, updateVehicle } from '@/api/vehicle'
import { fetchUsers } from '@/api/system'
import { buildVehiclePayload, buildVehicleQuery } from '@/utils/contracts'


const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const search = reactive({ plate: '' })
const userList = ref([])

const listWithOwner = computed(() =>
  list.value.map(v => ({
    ...v,
    owner_name: userList.value.find(u => u.id === v.owner_id)?.username || '—'
  }))
)

const dialogVisible = ref(false)
const formRef = ref(null)
const submitting = ref(false)
const editingId = ref(null)

const dialogTitle = computed(() => (editingId.value ? '编辑车辆' : '新增车辆'))

const form = reactive({
  plate_no: '', owner_id: null, vehicle_type: '', color: ''
})

const rules = computed(() => ({
  plate_no: [{ required: true, message: '请输入车牌号', trigger: 'blur' }],
  owner_id: editingId.value
    ? []
    : [{ required: true, message: '请选择用户', trigger: 'change' }]
}))

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '—'
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getVehicles(buildVehicleQuery(search, page.value, pageSize.value))
    list.value = res.data.items
    total.value = res.data.total
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
  if (!userList.value.length) loadUserList()
}

function resetSearch() {
  search.plate = ''
  page.value = 1
  fetchList()
}

async function loadUserList() {
  try {
    const res = await fetchUsers({ page: 1, page_size: 100, role: 'citizen' })
    userList.value = res.data.items || []
  } catch { /* handled by interceptor */ }
}

function openDialog(row) {
  editingId.value = row ? row.id : null
  Object.assign(form, row
    ? {
        plate_no: row.plate_no,
        owner_id: row.owner_id,
        vehicle_type: row.vehicle_type ?? '',
        color: row.color ?? ''
      }
    : { plate_no: '', owner_id: null, vehicle_type: '', color: '' })
  dialogVisible.value = true
  if (!editingId.value) { loadUserList() }
  nextTick(() => formRef.value?.clearValidate())
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const payload = buildVehiclePayload(form)
    if (editingId.value) {
      await updateVehicle(editingId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await createVehicle(payload)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch { /* handled */ }
  finally { submitting.value = false }
}

onMounted(fetchList)
</script>
