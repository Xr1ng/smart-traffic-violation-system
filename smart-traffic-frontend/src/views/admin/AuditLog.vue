<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">操作日志</h2>
    </div>

    <el-card>
      <el-form :inline="true" size="small" style="margin-bottom:16px">
        <el-form-item label="操作类型">
          <el-select v-model="filter.action" clearable placeholder="全部" style="width:140px">
            <el-option label="登录" value="login" />
            <el-option label="审核通过" value="approve" />
            <el-option label="审核驳回" value="reject" />
            <el-option label="图片上传" value="upload" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作人">
          <el-input v-model="filter.username" placeholder="输入用户名" clearable style="width:160px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchLogs">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="logs" border stripe>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
        </el-table-column>
        <el-table-column prop="username" label="操作人" width="100" />
        <el-table-column label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.action === 'login' ? 'info' : row.action === 'approve' ? 'success' : row.action === 'reject' ? 'danger' : 'warning'" size="small">
              {{ actionMap[row.action] || row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="操作详情" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP 地址" width="140" />
      </el-table>

      <div style="text-align:right;padding-top:16px">
        <el-pagination
          v-model:current-page="page"
          :total="total"
          :page-size="pageSize"
          layout="total, prev, pager, next"
          @current-change="fetchLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { fetchAuditLogs } from '@/api/system'

const page = ref(1)
const pageSize = ref(15)
const total = ref(0)
const logs = ref([])

const filter = reactive({ action: '', username: '' })
const actionMap = { login: '登录', approve: '审核通过', reject: '审核驳回', upload: '上传图片', logout: '登出' }

async function fetchLogs() {
  const res = await fetchAuditLogs({ page: page.value, page_size: pageSize, action: filter.action || undefined })
  logs.value = res.data.items
  total.value = res.data.total
}

fetchLogs()
</script>

<style scoped>
.page-container { }
.page-header { margin-bottom: 16px; }
.page-title { font-size: 20px; margin: 0; }
</style>
