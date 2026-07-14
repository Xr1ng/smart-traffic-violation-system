<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">违章列表</h2>
      <div style="display:flex;gap:12px">
        <el-button type="primary" @click="router.push('/admin/violations/upload')">
          上传违章证据
        </el-button>
        <el-button type="success" @click="exportData" :disabled="list.length === 0">
          <el-icon><Download /></el-icon>导出 Excel
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="table-toolbar">
      <div class="left">
        <el-input v-model="search.plate" placeholder="车牌号" clearable style="width:140px" />
        <el-input v-model="search.location" placeholder="违章地点" clearable style="width:140px" />
        <el-select v-model="search.type" placeholder="违章类型" clearable style="width:140px">
          <el-option label="闯红灯" value="闯红灯" />
          <el-option label="超速" value="超速" />
          <el-option label="违停" value="违停" />
          <el-option label="压线" value="压线" />
          <el-option label="逆行" value="逆行" />
        </el-select>
        <el-select v-model="search.status" placeholder="处理状态" clearable style="width:140px">
          <el-option label="待处理" value="pending" />
        </el-select>
        <el-date-picker
          v-model="search.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width:250px"
        />
        <el-button type="primary" @click="fetchList">查询</el-button>
        <el-button @click="resetSearch">重置</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="violation_no" label="违章编号" min-width="170" />
      <el-table-column prop="plate_no" label="车牌号" width="120" />
      <el-table-column prop="violation_type" label="违章类型" width="100" />
      <el-table-column prop="location_text" label="违章地点" min-width="160" />
      <el-table-column prop="occurred_at" label="违章时间" width="180" />
      <el-table-column prop="fine_amount" label="罚款（元）" width="100" />
      <el-table-column prop="points" label="扣分" width="80" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">{{ statusMap[row.status] || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="router.push(`/review/case/${row.case_id}`)">
            审核
          </el-button>
        </template>
      </el-table-column>
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchViolations } from '@/api/violation'
import { buildViolationQuery } from '@/utils/contracts'
import { exportToExcel, formatExportTime } from '@/utils/export'
import { Download } from '@element-plus/icons-vue'

const router = useRouter()
const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const statusMap = { pending: '待处理' }
function statusTagType(s) {
  return s === 'pending' ? 'warning' : 'info'
}

const search = reactive({
  plate: '', location: '', type: '', status: '', dateRange: null
})

async function fetchList() {
  loading.value = true
  try {
    const res = await fetchViolations(buildViolationQuery(search, page.value, pageSize.value))
    list.value = res.data.items
    total.value = res.data.total
  } catch { /* handled */ }
  finally { loading.value = false }
}

function resetSearch() {
  Object.keys(search).forEach(k => search[k] = k === 'dateRange' ? null : '')
  fetchList()
}

function exportData() {
  const columns = [
    { key: 'violation_no', label: '违章编号', width: 22 },
    { key: 'plate_no', label: '车牌号', width: 12 },
    { key: 'violation_type', label: '违章类型', width: 12 },
    { key: 'location_text', label: '违章地点', width: 24 },
    { key: 'occurred_at', label: '违章时间', width: 22 },
    { key: 'fine_amount', label: '罚款(元)', width: 12 },
    { key: 'points', label: '扣分', width: 8 },
    { key: 'status', label: '状态', width: 10 }
  ]
  const data = list.value.map(row => ({
    ...row,
    occurred_at: formatExportTime(row.occurred_at),
    status: statusMap[row.status] || row.status
  }))
  exportToExcel(data, columns, `违章记录_${new Date().toISOString().slice(0, 10)}`)
}

onMounted(fetchList)
</script>
