<template>
  <div class="page-container" style="max-width:800px">
    <div class="page-header">
      <h2 class="page-title">车辆绑定管理</h2>
    </div>

    <el-card style="margin-bottom:16px">
      <template #header><span>绑定车辆</span></template>
      <el-form :model="bindForm" :rules="bindRules" ref="bindRef" label-width="100px" :inline="true">
        <el-form-item label="车牌号" prop="plate_no">
          <el-input v-model="bindForm.plate_no" placeholder="如：粤A12345" style="width:200px" />
        </el-form-item>
        <el-form-item label="车辆类型">
          <el-select v-model="bindForm.vehicle_type" style="width:160px">
            <el-option v-for="t in vehicleTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="binding" @click="handleBind">绑定</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header><span>已绑定车辆</span></template>
      <el-table :data="vehicles" stripe>
        <el-table-column prop="plate_no" label="车牌号" width="140" />
        <el-table-column prop="vehicle_type" label="车辆类型" width="120" />
        <el-table-column prop="color" label="颜色" width="80" />
        <el-table-column label="绑定时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" type="primary" text @click="viewViolations(row.plate_no)">查违章</el-button>
            <el-button size="small" type="danger" text @click="handleUnbind(row)">解绑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="vehicles.length === 0" description="尚未绑定车辆" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { getVehicles, createVehicle } from '@/api/vehicle'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const bindRef = ref(null)
const binding = ref(false)
const vehicles = ref([])

async function loadVehicles() {
  const uid = JSON.parse(localStorage.getItem('userInfo') || '{}').id
  if (uid) {
    const res = await getVehicles({ page_size: 100 })
    vehicles.value = (res.data.items || []).filter(v => v.owner_id === uid)
  }
}
loadVehicles()
const vehicleTypes = ['小型轿车', 'SUV', '货车', '摩托车', '新能源']

const bindForm = reactive({ plate_no: '', vehicle_type: '小型轿车' })
const bindRules = {
  plate_no: [{ required: true, message: '请输入车牌号', trigger: 'blur' }]
}

function formatTime(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }

async function handleBind() {
  const valid = await bindRef.value.validate().catch(() => false)
  if (!valid) return
  binding.value = true
  try {
    const uid = JSON.parse(localStorage.getItem('userInfo') || '{}').id
    await createVehicle({ plate_no: bindForm.plate_no, vehicle_type: bindForm.vehicle_type, owner_id: uid, color: '白' })
    ElMessage.success('绑定成功')
    bindForm.plate_no = ''
    loadVehicles()
  } catch { ElMessage.error('绑定失败') }
  bindForm.plate_no = ''
  binding.value = false
  ElMessage.success('车辆绑定成功')
}

async function handleUnbind(row) {
  await ElMessageBox.confirm(`确定要解绑车辆 ${row.plate_no} 吗？`, '确认', { type: 'warning' })
  vehicles.value = vehicles.value.filter(v => v.id !== row.id)
  ElMessage.success('已解绑')
}

function viewViolations(plateNo) {
  router.push('/citizen/my-violations')
}
</script>

<style scoped>
.page-container { }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; margin: 0; }
</style>
