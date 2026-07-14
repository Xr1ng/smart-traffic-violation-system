<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">违章查询</h2>
      <el-button type="success" @click="exportData" :disabled="list.length === 0">
        <el-icon><Download /></el-icon>导出 Excel
      </el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="plate_no" label="车牌号" width="120" />
      <el-table-column prop="violation_type" label="违章类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.violation_type === '闯红灯' ? 'danger' : 'warning'" size="small">{{ row.violation_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="location_text" label="违章地点" min-width="180" show-overflow-tooltip />
      <el-table-column prop="occurred_at" label="违章时间" width="170">
        <template #default="{ row }">{{ formatTime(row.occurred_at) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'pending'" type="warning" size="small">待处理</el-tag>
          <el-tag v-else type="info" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="points" label="扣分" width="70" align="center" />
      <el-table-column prop="fine_amount" label="罚款(元)" width="90" align="center" />
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:16px">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @change="fetchList"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchOwnerViolations } from '@/api/violation'
import { exportToExcel, formatExportTime } from '@/utils/export'
import { Download } from '@element-plus/icons-vue'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

function formatTime(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }

async function fetchList() {
  loading.value = true
  try {
    const uid = JSON.parse(localStorage.getItem('userInfo') || '{}').id
    if (uid) {
      const res = await fetchOwnerViolations(uid)
      list.value = res.data.items
      total.value = res.data.total
    }
  } catch {}
  loading.value = false
}

onMounted(fetchList)

function exportData() {
  const columns = [
    { key: 'plate_no', label: '车牌号', width: 12 },
    { key: 'violation_type', label: '违章类型', width: 12 },
    { key: 'location_text', label: '违章地点', width: 24 },
    { key: 'occurred_at', label: '违章时间', width: 22 },
    { key: 'fine_amount', label: '罚款(元)', width: 12 },
    { key: 'points', label: '扣分', width: 8 }
  ]
  const statusMap = { pending: '待处理' }
  const data = list.value.map(row => ({
    ...row,
    occurred_at: formatExportTime(row.occurred_at),
    status: statusMap[row.status] || row.status
  }))
  exportToExcel(data, columns, `我的违章_${new Date().toISOString().slice(0, 10)}`)
}
</script>

<style scoped>
.page-container { }
.page-header { margin-bottom: 16px; }
.page-title { font-size: 20px; margin: 0; }
</style>
