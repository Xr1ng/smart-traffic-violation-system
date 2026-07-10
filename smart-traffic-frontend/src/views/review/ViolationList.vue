<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">违章记录管理</h2>
      <el-button type="primary" @click="handleExport"><el-icon><Download /></el-icon>导出 Excel</el-button>
    </div>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filter" size="small">
        <el-form-item label="车牌号">
          <el-input v-model="filter.plate_no" placeholder="输入车牌号" clearable />
        </el-form-item>
        <el-form-item label="违章类型">
          <el-select v-model="filter.violation_type" placeholder="全部" clearable style="width:140px">
            <el-option v-for="t in types" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filter.status" placeholder="全部" clearable style="width:120px">
            <el-option label="待处理" value="pending" />
            <el-option label="已处理" value="handled" />
            <el-option label="已撤销" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card style="margin-top:16px">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="violation_no" label="编号" width="140" />
        <el-table-column prop="plate_no" label="车牌号" width="120" />
        <el-table-column prop="violation_type" label="违章类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.violation_type === '闯红灯' ? 'danger' : 'warning'" size="small">{{ row.violation_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location_text" label="地点" min-width="180" show-overflow-tooltip />
        <el-table-column prop="occurred_at" label="发生时间" width="170">
          <template #default="{ row }">{{ formatTime(row.occurred_at) }}</template>
        </el-table-column>
        <el-table-column prop="fine_amount" label="罚款(元)" width="90" align="center" />
        <el-table-column prop="points" label="扣分" width="70" align="center" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'handled' ? 'success' : row.status === 'pending' ? 'warning' : 'info'" size="small">
              {{ statusMap[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner_name" label="车主" width="80" />
      </el-table>

      <div style="padding:16px 0 0;text-align:right">
        <el-pagination
          v-model:current-page="page"
          :total="total"
          :page-size="pageSize"
          layout="total, prev, pager, next"
          @current-change="fetchList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { fetchViolations as getViolations } from '@/api/violation'
import { ElMessage } from 'element-plus'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const types = ['闯红灯', '违停', '压线', '逆行', '超速', '占用应急车道']
const statusMap = { pending: '待处理', handled: '已处理', cancelled: '已撤销' }

const filter = reactive({ plate_no: '', violation_type: '', status: '' })

function formatTime(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }

async function fetchList() {
  loading.value = true
  try {
    const res = await getViolations({ ...filter, page: page.value, page_size: pageSize.value })
    list.value = res.data.items
    total.value = res.data.total
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function resetFilter() {
  Object.assign(filter, { plate_no: '', violation_type: '', status: '' })
  page.value = 1
  fetchList()
}

function handleExport() {
  ElMessage.success('正在导出 Excel，请稍候...')
}

onMounted(fetchList)
</script>

<style scoped>
.page-container { }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { margin: 0; font-size: 20px; }
.filter-card { margin-bottom: 0; }
</style>
