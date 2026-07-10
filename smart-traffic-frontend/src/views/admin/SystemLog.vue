<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">系统日志</h2>
    </div>

    <div class="table-toolbar">
      <div class="left">
        <el-select v-model="search.type" placeholder="操作类型" clearable style="width:140px">
          <el-option label="登录" value="login" />
          <el-option label="查询" value="query" />
          <el-option label="新增" value="create" />
          <el-option label="修改" value="update" />
          <el-option label="删除" value="delete" />
        </el-select>
        <el-date-picker
          v-model="search.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
        />
        <el-button type="primary" @click="fetchList">查询</el-button>
      </div>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column type="index" label="#" width="50" />
      <el-table-column prop="username" label="操作用户" width="120" />
      <el-table-column prop="action" label="操作类型" width="100" />
      <el-table-column prop="detail" label="操作详情" min-width="280" show-overflow-tooltip />
      <el-table-column prop="ip" label="IP 地址" width="140" />
      <el-table-column prop="created_at" label="操作时间" width="160" />
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
import { fetchAuditLogs } from '@/api/system'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(15)
const total = ref(0)
const search = reactive({ type: '', dateRange: null })

async function fetchList() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (search.type) params.action = search.type
    const res = await fetchAuditLogs(params)
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch { /* handled */ }
  finally { loading.value = false }
}

onMounted(fetchList)
</script>
