<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">举报进度</h2>
      <el-button type="primary" @click="router.push('/citizen/report')">发起新举报</el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column label="图片" width="90">
        <template #default="{ row }">
          <el-image v-if="row.image_url" :src="row.image_url" style="width:50px;height:50px;border-radius:4px" fit="cover" :preview-src-list="[row.image_url]" />
        </template>
      </el-table-column>
      <el-table-column prop="description" label="举报描述" min-width="180" show-overflow-tooltip />
      <el-table-column prop="location_text" label="违章地点" width="180" show-overflow-tooltip />
      <el-table-column prop="captured_at" label="违章时间" width="170">
        <template #default="{ row }">{{ formatTime(row.captured_at) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'pending_human_review'" type="warning">待审核</el-tag>
          <el-tag v-else-if="row.status === 'approved'" type="success">已通过</el-tag>
          <el-tag v-else-if="row.status === 'rejected'" type="danger">已驳回</el-tag>
          <el-tag v-else type="info">{{ statusMap[row.status] || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="奖励" width="100">
        <template #default="{ row }">
          <span v-if="row.reward" style="color:#e6a23c;font-weight:bold">+{{ row.reward }}元</span>
          <span v-else>—</span>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchCases } from '@/api/case'

const router = useRouter()
const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const statusMap = {
  uploaded: '待识别', detecting: '识别中', ai_reviewing: 'AI 审核中',
  pending_human_review: '待审核', approved: '已通过', rejected: '已驳回'
}

function formatTime(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }

async function fetchList() {
  loading.value = true
  try {
    const res = await fetchCases({ source_type: 'citizen', page: page.value, page_size: pageSize })
    list.value = res.data.items
    total.value = res.data.total
  } catch {}
  loading.value = false
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
.page-title { font-size: 20px; margin: 0; }
</style>
