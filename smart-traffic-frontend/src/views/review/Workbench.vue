<template>
  <div class="workbench">
    <!-- 筛选工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-radio-group v-model="filter.status" size="small" @change="fetchCases">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="pending_human_review">待审核</el-radio-button>
          <el-radio-button value="approved">已通过</el-radio-button>
          <el-radio-button value="rejected">已驳回</el-radio-button>
        </el-radio-group>
        <el-select v-model="filter.source_type" placeholder="来源" clearable size="small" style="width:120px;margin-left:12px" @change="fetchCases">
          <el-option label="随手拍" value="citizen" />
          <el-option label="摄像头" value="camera" />
          <el-option label="后台上传" value="admin" />
        </el-select>
        <el-input v-model="filter.keyword" placeholder="搜索案件号/车牌/地点" size="small" clearable style="width:240px;margin-left:12px" @keyup.enter="fetchCases" @clear="fetchCases" />
      </div>
      <div class="toolbar-right">
        <el-tag type="danger" v-if="pendingTotal">待审核：{{ pendingTotal }} 件</el-tag>
        <el-button size="small" @click="fetchCases" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 案件卡片流 -->
    <div v-loading="loading" class="card-grid">
      <el-empty v-if="!loading && cases.length === 0" description="暂无案件" />

      <el-card
        v-for="item in cases"
        :key="item.id"
        :class="['case-card', { 'is-pending': item.status === 'pending_human_review' }]"
        shadow="hover"
        @click="openDetail(item.id)"
      >
        <!-- 状态标签 + 案件号 -->
        <div class="card-header">
          <el-tag :type="statusType(item.status)" size="small">{{ statusText(item.status) }}</el-tag>
          <span class="case-no">{{ item.case_no }}</span>
          <span class="case-source">{{ sourceIcon(item.source_type) }} {{ item.source_desc }}</span>
        </div>

        <!-- 图片预览 -->
        <div class="card-image">
          <el-image :src="item.media?.original_url" fit="cover" style="width:100%;height:180px" :preview-src-list="[item.media?.original_url]">
            <template #error>
              <div class="img-placeholder"><el-icon :size="40"><Picture /></el-icon></div>
            </template>
          </el-image>
        </div>

        <!-- 关键信息 -->
        <div class="card-info">
          <div class="info-row">
            <el-icon><MapLocation /></el-icon>
            <span>{{ item.location_text }}</span>
          </div>
          <div class="info-row">
            <el-icon><Clock /></el-icon>
            <span>{{ formatTime(item.captured_at) }}</span>
          </div>
          <div class="info-row" v-if="item.plate_no">
            <el-icon><Tickets /></el-icon>
            <span>{{ item.plate_no }}</span>
          </div>
        </div>

        <!-- AI 初审标签 -->
        <div class="card-footer" v-if="item.ai_review">
          <el-tag :type="aiTagType(item.ai_review.conclusion)" size="small" effect="dark">
            {{ aiConclusionText(item.ai_review.conclusion) }}
          </el-tag>
          <span class="ai-mode">{{ item.ai_review.review_mode === 'vision_llm' ? '多模态复核' : 'AI 初审' }}</span>
          <span class="ai-confidence">置信度 {{ (item.ai_review.ai_confidence * 100).toFixed(0) }}%</span>
        </div>
        <div class="card-footer" v-else>
          <el-tag size="small" type="info">AI 处理中...</el-tag>
        </div>
      </el-card>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :total="total"
        :page-size="pageSize"
        layout="prev, pager, next"
        @current-change="fetchCases"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCases } from '@/api/case'
import { ElMessage } from 'element-plus'

const router = useRouter()
const cases = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const pendingTotal = ref(0)

const filter = reactive({
  status: 'pending_human_review',
  source_type: '',
  keyword: ''
})

// 状态映射
const statusMap = {
  uploaded: '待识别', detecting: '识别中', ai_reviewing: 'AI 初审中',
  pending_human_review: '待审核', approved: '已通过', rejected: '已驳回',
  archived: '已归档', notified: '已通知'
}
const statusTypeMap = {
  uploaded: 'info', detecting: 'warning', ai_reviewing: 'warning',
  pending_human_review: 'danger', approved: 'success', rejected: 'info',
  archived: '', notified: 'success'
}

function statusText(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function sourceIcon(s) { return s === 'citizen' ? '📱' : s === 'camera' ? '📷' : '👤' }
function formatTime(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }

const aiConclusionMap = { suggest_approve: '建议通过', need_review: '建议复核', suggest_reject: '建议驳回' }
const aiTagTypeMap = { suggest_approve: 'success', need_review: 'warning', suggest_reject: 'danger' }

function aiConclusionText(c) { return aiConclusionMap[c] || c }
function aiTagType(c) { return aiTagTypeMap[c] || 'info' }

async function fetchCases() {
  loading.value = true
  try {
    const res = await getCases({
      status: filter.status,
      source_type: filter.source_type,
      keyword: filter.keyword,
      page: page.value,
      page_size: pageSize.value
    })
    cases.value = res.data.list
    total.value = res.data.total
    // 统计待审核数
    if (!filter.status || filter.status === 'pending_human_review') {
      const pendingRes = await getCases({ status: 'pending_human_review', page: 1, page_size: 1 })
      pendingTotal.value = pendingRes.data.total
    }
  } catch (e) { console.error('[Workbench] fetchCases failed', e); ElMessage.error('加载案件失败') }
  finally { loading.value = false }
}

function openDetail(id) {
  router.push(`/review/case/${id}`)
}

// 定时轮询（每 15 秒刷新待审核）
let pollTimer = null
onMounted(() => {
  fetchCases()
  pollTimer = setInterval(() => {
    if (filter.status === 'pending_human_review' || !filter.status) {
      fetchCases()
    }
  }, 15000)
})
onUnmounted(() => clearInterval(pollTimer))
</script>

<style scoped>
.workbench { display: flex; flex-direction: column; gap: 16px; }
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.toolbar-right { display: flex; align-items: center; gap: 12px; }

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  min-height: 200px;
}
.case-card {
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}
.case-card:hover { transform: translateY(-2px); }
.case-card.is-pending { border-color: #f56c6c; }

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.case-no { font-size: 12px; color: var(--text-secondary); }
.case-source { font-size: 12px; color: var(--text-secondary); margin-left: auto; }

.card-image {
  border-radius: 4px;
  overflow: hidden;
  background: var(--bg-color);
  margin-bottom: 12px;
}
.img-placeholder {
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}
.info-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}
.ai-mode { font-size: 12px; color: var(--text-secondary); }
.ai-confidence { font-size: 12px; color: var(--text-secondary); margin-left: auto; }

.pagination {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}
</style>
