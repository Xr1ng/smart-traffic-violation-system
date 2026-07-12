<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">操作日志</h2>
      <span class="page-desc">记录所有用户的操作行为，便于追溯审计</span>
    </div>

    <el-card>
      <el-form :inline="true" size="small" style="margin-bottom:16px">
        <el-form-item label="操作类型">
          <el-select v-model="filter.action" clearable placeholder="全部" style="width:140px">
            <el-option label="登录" value="login" />
            <el-option label="审核通过" value="approve" />
            <el-option label="审核驳回" value="reject" />
            <el-option label="图片上传" value="upload" />
            <el-option label="新增" value="create" />
            <el-option label="修改" value="update" />
            <el-option label="删除" value="delete" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="fetchLogs">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="logs" border stripe v-loading="loading">
        <el-table-column type="index" label="#" width="55" />
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
        </el-table-column>
        <el-table-column prop="actor_id" label="操作人ID" width="110" />
        <el-table-column label="操作类型" width="110">
          <template #default="{ row }">
            <el-tag
              :type="actionTagType(row.action)"
              size="small"
            >
              {{ actionMap[row.action] || row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="操作详情" min-width="220" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP 地址" width="140" />
      </el-table>

      <div style="text-align:right;padding-top:16px">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @current-change="fetchLogs"
          @size-change="fetchLogs"
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
const loading = ref(false)

const filter = reactive({ action: '' })

const actionMap = {
  login: '登录', logout: '登出',
  approve: '审核通过', reject: '审核驳回',
  create: '新增', update: '修改', delete: '删除',
  upload: '上传图片', query: '查询'
}

function actionTagType(action) {
  const map = {
    login: 'info', logout: 'info',
    approve: 'success', reject: 'danger',
    create: 'primary', update: 'warning', delete: 'danger',
    upload: 'warning', query: ''
  }
  return map[action] || ''
}

function resetFilter() {
  filter.action = ''
  page.value = 1
  fetchLogs()
}

async function fetchLogs() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filter.action) params.action = filter.action
    const res = await fetchAuditLogs(params)
    logs.value = res.data.items
    total.value = res.data.total
  } catch { /* handled */ }
  finally { loading.value = false }
}

fetchLogs()
</script>

<style scoped>
.page-container { }
.page-header { margin-bottom: 16px; display: flex; align-items: baseline; gap: 12px; }
.page-title { font-size: 20px; margin: 0; }
.page-desc { color: #909399; font-size: 13px; }
</style>
