<template>
  <div class="workbench">
    <!-- 筛选工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-radio-group v-model="filter.status" size="small" @change="fetchCases">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="uploaded">待初审</el-radio-button>
          <el-radio-button value="pending_human_review">待终审</el-radio-button>
          <el-radio-button value="notified">已通知</el-radio-button>
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
        <el-button size="small" @click="batchMode = !batchMode" :type="batchMode ? 'danger' : 'default'">
          {{ batchMode ? '退出批量' : '批量审核' }}
        </el-button>
        <el-button size="small" @click="fetchCases" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div class="batch-bar" v-if="batchMode && selectedIds.length > 0">
      <span class="batch-info">已选 <strong>{{ selectedIds.length }}</strong> 件</span>
      <el-button type="success" size="small" @click="batchApprove" :loading="batchLoading">
        <el-icon><Check /></el-icon>批量通过
      </el-button>
      <el-button type="danger" size="small" @click="batchReject" :loading="batchLoading">
        <el-icon><Close /></el-icon>批量驳回
      </el-button>
      <el-button size="small" @click="selectedIds = []">取消选择</el-button>
    </div>

    <!-- 案件卡片流 -->
    <div v-loading="loading" class="card-grid">
      <el-empty v-if="!loading && cases.length === 0" description="暂无案件" />

      <el-card
        v-for="item in cases"
        :key="item.id"
        :class="['case-card', { 'is-pending': ['uploaded', 'pending_human_review'].includes(item.status), 'is-selected': selectedIds.includes(item.id) }]"
        shadow="hover"
        @click="onCardClick(item.id)"
      >
        <!-- 批量选择框 -->
        <div v-if="batchMode" class="batch-check" @click.stop>
          <el-checkbox :model-value="selectedIds.includes(item.id)" @change="toggleSelect(item.id)" />
        </div>
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
          <span class="ai-confidence">置信度 {{ (item.ai_review.ai_confidence * 100).toFixed(0) }}%</span>
        </div>
        <div class="card-footer" v-else>
          <el-tag size="small" type="info">{{ caseAiFallbackText(item.status) }}</el-tag>
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
import { useUserStore } from '@/stores/user'
import { fetchCases as getCases } from '@/api/case'
import { approveCase, rejectCase } from '@/api/case'
import { fetchProtectedMediaUrl } from '@/api/media'
import {
  caseAiFallbackText,
  createLatestRequestGuard,
  loadProtectedMediaUrls,
  releaseProtectedMediaUrls
} from '@/utils/contracts'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const cases = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const pendingTotal = ref(0)
const mediaRequestGuard = createLatestRequestGuard()

// 批量审核
const batchMode = ref(false)
const selectedIds = ref([])
const batchLoading = ref(false)

function onCardClick(id) {
  if (batchMode.value) {
    toggleSelect(id)
  } else {
    openDetail(id)
  }
}

function toggleSelect(id) {
  const i = selectedIds.value.indexOf(id)
  if (i > -1) selectedIds.value.splice(i, 1)
  else selectedIds.value.push(id)
}

async function batchApprove() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确认通过选中的 ${selectedIds.value.length} 件案件？`, '批量审核', { type: 'warning' })
  } catch { return }
  batchLoading.value = true
  try {
    await Promise.all(selectedIds.value.map(id => approveCase(id, { review_comment: '批量审核通过' })))
    ElMessage.success(`已通过 ${selectedIds.value.length} 件`)
    selectedIds.value = []
    fetchCases()
  } catch { ElMessage.error('批量操作失败') }
  finally { batchLoading.value = false }
}

async function batchReject() {
  if (selectedIds.value.length === 0) return
  let comment = '批量审核驳回'
  try {
    const result = await ElMessageBox.prompt('驳回原因', '批量驳回', { type: 'warning', inputPlaceholder: '请填写驳回原因' })
    comment = result.value || comment
  } catch { return }
  batchLoading.value = true
  try {
    await Promise.all(selectedIds.value.map(id => rejectCase(id, { review_comment: comment })))
    ElMessage.success(`已驳回 ${selectedIds.value.length} 件`)
    selectedIds.value = []
    fetchCases()
  } catch { ElMessage.error('批量操作失败') }
  finally { batchLoading.value = false }
}

const filter = reactive({
  status: '',
  source_type: '',
  keyword: ''
})

// 状态映射
const statusMap = {
  uploaded: '待初审', detecting: '识别中', ai_reviewing: 'AI 初审中',
  pending_human_review: '待终审', approved: '已通过', rejected: '已驳回',
  archived: '已归档', notified: '已通知'
}
const statusTypeMap = {
  uploaded: 'danger', detecting: 'warning', ai_reviewing: 'warning',
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
  const requestGeneration = mediaRequestGuard.begin()
  loading.value = true
  try {
    const res = await getCases({
      status: filter.status,
      source_type: filter.source_type,
      keyword: filter.keyword,
      page: page.value,
      page_size: pageSize.value
    })
    let nextPendingTotal = 0
    if (!filter.status || ['uploaded', 'pending_human_review'].includes(filter.status)) {
      const [uploadedRes, pendingRes] = await Promise.all([
        getCases({ status: 'uploaded', page: 1, page_size: 1 }),
        getCases({ status: 'pending_human_review', page: 1, page_size: 1 })
      ])
      nextPendingTotal = uploadedRes.data.total + pendingRes.data.total
    }
    const nextCases = await Promise.all(
      res.data.items.map(async item => ({
        ...item,
        media: await loadProtectedMediaUrls(item.media, fetchProtectedMediaUrl)
      }))
    )
    if (!mediaRequestGuard.isCurrent(requestGeneration)) {
      nextCases.forEach(item => releaseProtectedMediaUrls(item.media))
      return
    }
    cases.value.forEach(item => releaseProtectedMediaUrls(item.media))
    cases.value = nextCases
    total.value = res.data.total
    pendingTotal.value = nextPendingTotal
  } catch (e) {
    if (mediaRequestGuard.isCurrent(requestGeneration)) {
      console.error('[Workbench] fetchCases failed', e)
      ElMessage.error('加载案件失败')
    }
  } finally {
    if (mediaRequestGuard.isCurrent(requestGeneration)) loading.value = false
  }
}

function openDetail(id) {
  const path = userStore.role === 'admin' ? `/admin/violations/${id}` : `/review/case/${id}`
  router.push(path)
}

// 定时轮询（每 15 秒刷新待审核）
let pollTimer = null
onMounted(() => {
  fetchCases()
  pollTimer = setInterval(() => {
    if (!filter.status || ['uploaded', 'pending_human_review'].includes(filter.status)) {
      fetchCases()
    }
  }, 15000)
})
onUnmounted(() => {
  mediaRequestGuard.invalidate()
  clearInterval(pollTimer)
  cases.value.forEach(item => releaseProtectedMediaUrls(item.media))
})
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

.batch-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--el-color-primary-light-9);
  border-radius: 8px;
}
.batch-info { font-size: 14px; color: var(--text-secondary); }

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
  position: relative;
}
.case-card:hover { transform: translateY(-2px); }
.case-card.is-pending { border-color: #f56c6c; }
.case-card.is-selected { border-color: var(--el-color-primary); background: var(--el-color-primary-light-9); }

.batch-check {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 10;
  background: rgba(255,255,255,0.9);
  border-radius: 4px;
  padding: 2px 4px;
}

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
