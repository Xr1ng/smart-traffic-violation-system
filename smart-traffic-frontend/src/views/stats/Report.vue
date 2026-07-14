<template>
  <div class="report-page">
    <header class="page-header no-print">
      <div class="title-group">
        <el-button :icon="ArrowLeft" circle title="返回" @click="router.back()" />
        <div>
          <h2 class="page-title">智能分析报告</h2>
          <p class="page-subtitle">基于平台聚合统计数据生成</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button :icon="Clock" @click="handleOpenHistory">历史报告</el-button>
        <el-button v-if="report" :icon="Printer" @click="handlePrint">打印 PDF</el-button>
      </div>
    </header>

    <el-drawer
      v-model="historyOpen"
      title="历史报告"
      direction="rtl"
      size="min(440px, 100vw)"
      class="history-drawer"
      @open="loadHistory"
    >
      <div class="history-filter">
        <el-date-picker
          v-model="historyDateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="统计开始日期"
          end-placeholder="统计结束日期"
          unlink-panels
          clearable
        />
        <div class="history-filter-actions">
          <el-tooltip content="查询" placement="bottom">
            <el-button type="primary" :icon="Search" circle @click="handleHistorySearch" />
          </el-tooltip>
          <el-tooltip content="重置" placement="bottom">
            <el-button :icon="RefreshLeft" circle @click="handleHistoryReset" />
          </el-tooltip>
        </div>
      </div>

      <el-alert
        v-if="historyError"
        class="history-alert"
        type="error"
        :title="historyError"
        :closable="false"
        show-icon
      />

      <el-skeleton v-if="historyLoading" :rows="8" animated />
      <el-empty v-else-if="!historyItems.length" description="暂无历史报告" />
      <template v-else>
        <div class="history-list" role="list">
          <button
            v-for="item in historyItems"
            :key="item.id"
            class="history-row"
            type="button"
            :disabled="historyDetailLoadingId === item.id"
            @click="handleSelectHistory(item)"
          >
            <el-icon class="history-row-icon"><Document /></el-icon>
            <span class="history-row-content">
              <strong>{{ item.title }}</strong>
              <span>{{ formatDate(item.start_time) }} 至 {{ formatDate(item.end_time) }}</span>
              <small>生成于 {{ formatDateTime(item.generated_at) }}</small>
            </span>
            <el-icon v-if="historyDetailLoadingId === item.id" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><ArrowRight /></el-icon>
          </button>
        </div>
        <el-pagination
          v-model:current-page="historyPage"
          class="history-pagination"
          layout="prev, pager, next"
          :page-size="historyPageSize"
          :total="historyTotal"
          hide-on-single-page
          @current-change="loadHistory"
        />
      </template>
    </el-drawer>

    <section class="report-toolbar no-print">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        :clearable="false"
        unlink-panels
      />
      <el-button
        type="primary"
        :icon="Document"
        :loading="loading"
        @click="handleGenerate"
      >
        生成新报告
      </el-button>
    </section>

    <el-alert
      v-if="errorMessage"
      class="report-alert no-print"
      type="error"
      :title="errorMessage"
      :closable="false"
      show-icon
    />

    <div v-if="loading" class="report-sheet loading-sheet">
      <el-skeleton :rows="12" animated />
    </div>

    <article v-else-if="report" class="report-sheet">
      <div class="report-heading">
        <p class="report-kicker">TRAFFIC ANALYSIS</p>
        <h1>{{ report.title }}</h1>
        <div class="report-meta">
          <span>统计周期：{{ formatDate(report.start_time) }} 至 {{ formatDate(report.end_time) }}</span>
          <span>生成时间：{{ formatDateTime(report.generated_at) }}</span>
          <span>生成者：{{ report.author }}</span>
        </div>
      </div>

      <section class="report-section">
        <h2><span>01</span>执行摘要</h2>
        <p>{{ report.summary }}</p>
      </section>

      <section class="report-section two-column">
        <div>
          <h2><span>02</span>趋势分析</h2>
          <p>{{ report.trend_analysis }}</p>
        </div>
        <div>
          <h2><span>03</span>热点分析</h2>
          <p>{{ report.hotspot_analysis }}</p>
        </div>
      </section>

      <section class="report-section two-column list-section">
        <div>
          <h2><span>04</span>风险提示</h2>
          <ul v-if="report.risk_alerts.length">
            <li v-for="item in report.risk_alerts" :key="item">{{ item }}</li>
          </ul>
          <p v-else class="muted">本期未识别出明确风险提示。</p>
        </div>
        <div>
          <h2><span>05</span>治理建议</h2>
          <ol v-if="report.recommendations.length">
            <li v-for="item in report.recommendations" :key="item">{{ item }}</li>
          </ol>
          <p v-else class="muted">本期暂无补充治理建议。</p>
        </div>
      </section>

      <section class="report-section evidence-section">
        <h2><span>06</span>数据依据</h2>
        <div class="metric-grid">
          <div class="metric"><strong>{{ snapshot.overview.total_violations }}</strong><span>违章记录</span></div>
          <div class="metric"><strong>{{ snapshot.overview.total_cases }}</strong><span>案件总量</span></div>
          <div class="metric"><strong>{{ snapshot.overview.approve_rate }}%</strong><span>审核通过率</span></div>
          <div class="metric"><strong>{{ snapshot.overview.pending_count }}</strong><span>待审核</span></div>
        </div>

        <div class="evidence-grid">
          <div class="evidence-table">
            <h3>高发违章类型</h3>
            <div v-for="item in snapshot.violation_types.slice(0, 5)" :key="item.name" class="data-row">
              <span>{{ item.name }}</span><strong>{{ item.value }} 件 · {{ item.percentage }}%</strong>
            </div>
            <p v-if="!snapshot.violation_types.length" class="muted">暂无数据</p>
          </div>
          <div class="evidence-table">
            <h3>高发地点</h3>
            <div v-for="item in snapshot.locations.slice(0, 5)" :key="item.name" class="data-row">
              <span>{{ item.name || '未标注地点' }}</span><strong>{{ item.value }} 件</strong>
            </div>
            <p v-if="!snapshot.locations.length" class="muted">暂无数据</p>
          </div>
        </div>
      </section>

      <footer class="report-footer">
        本报告由 AI 根据平台聚合统计数据生成，仅用于交通管理分析参考。
      </footer>
    </article>

    <el-empty
      v-else
      class="report-empty no-print"
      description="选择统计周期后生成交通违章综合分析报告"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  ArrowRight,
  Clock,
  Document,
  Loading,
  Printer,
  RefreshLeft,
  Search
} from '@element-plus/icons-vue'
import {
  fetchReportDetail as fetchReportDetailApi,
  fetchReportHistory as fetchReportHistoryApi,
  generateReport as generateReportApi
} from '@/api/statistics'
import { buildReportHistoryQuery, buildReportRequest } from '@/utils/contracts'

const route = useRoute()
const router = useRouter()

function defaultRange() {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 29)
  return [start, end]
}

function rangeFromQuery() {
  if (!route.query.start_time || !route.query.end_time) return defaultRange()
  const start = new Date(String(route.query.start_time))
  const end = new Date(String(route.query.end_time))
  return Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())
    ? defaultRange()
    : [start, end]
}

const dateRange = ref(rangeFromQuery())
const loading = ref(false)
const report = ref(null)
const errorMessage = ref('')
const historyOpen = ref(false)
const historyLoading = ref(false)
const historyDetailLoadingId = ref('')
const historyError = ref('')
const historyDateRange = ref([])
const historyItems = ref([])
const historyPage = ref(1)
const historyPageSize = 20
const historyTotal = ref(0)
const snapshot = computed(() => report.value?.statistics_snapshot ?? {
  overview: {}, violation_types: [], locations: []
})

async function handleGenerate() {
  errorMessage.value = ''
  loading.value = true
  try {
    const response = await generateReportApi(buildReportRequest(dateRange.value))
    report.value = response.data || response
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '报告生成失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function handleOpenHistory() {
  historyPage.value = 1
  historyOpen.value = true
}

async function loadHistory() {
  historyError.value = ''
  historyLoading.value = true
  try {
    const params = buildReportHistoryQuery(
      historyDateRange.value,
      historyPage.value,
      historyPageSize
    )
    const response = await fetchReportHistoryApi(params)
    const data = response.data || response
    historyItems.value = data.items || []
    historyTotal.value = data.total || 0
  } catch (error) {
    historyError.value = error.response?.data?.detail || '历史报告加载失败，请稍后重试'
  } finally {
    historyLoading.value = false
  }
}

function handleHistorySearch() {
  historyPage.value = 1
  loadHistory()
}

function handleHistoryReset() {
  historyDateRange.value = []
  historyPage.value = 1
  loadHistory()
}

async function handleSelectHistory(item) {
  historyError.value = ''
  historyDetailLoadingId.value = item.id
  try {
    const response = await fetchReportDetailApi(item.id)
    report.value = response.data || response
    errorMessage.value = ''
    historyOpen.value = false
  } catch (error) {
    historyError.value = error.response?.data?.detail || '历史报告读取失败，请稍后重试'
  } finally {
    historyDetailLoadingId.value = ''
  }
}

function handlePrint() {
  window.print()
}

function formatDate(value) {
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'long' }).format(new Date(value))
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium', timeStyle: 'short'
  }).format(new Date(value))
}
</script>

<style scoped>
.report-page { max-width: 1120px; margin: 0 auto; }
.page-header,
.report-toolbar,
.title-group,
.header-actions,
.report-meta,
.data-row { display: flex; align-items: center; }
.page-header { justify-content: space-between; gap: 16px; margin-bottom: 14px; }
.title-group { gap: 12px; }
.header-actions { gap: 10px; }
.page-title { margin: 0; font-size: 20px; font-weight: 650; }
.page-subtitle { margin: 3px 0 0; color: #909399; font-size: 12px; }
.report-toolbar {
  gap: 10px;
  padding: 12px;
  margin-bottom: 14px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fff;
}
.report-alert { margin-bottom: 14px; }
.report-sheet {
  min-height: 680px;
  padding: 42px 52px 28px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  color: #25282d;
}
.loading-sheet { padding-top: 64px; }
.report-heading { padding-bottom: 24px; border-bottom: 2px solid #1f4e5f; }
.report-kicker { margin: 0 0 8px; color: #1f7a8c; font-size: 11px; font-weight: 700; }
.report-heading h1 { margin: 0 0 14px; font-size: 30px; font-weight: 700; }
.report-meta { flex-wrap: wrap; gap: 6px 22px; color: #606266; font-size: 12px; }
.report-section { padding: 24px 0; border-bottom: 1px solid #ebeef5; break-inside: avoid; }
.report-section h2 { margin: 0 0 13px; font-size: 17px; }
.report-section h2 span { margin-right: 9px; color: #1f7a8c; font-size: 12px; }
.report-section p { margin: 0; line-height: 1.9; white-space: pre-wrap; }
.two-column { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 36px; }
.list-section ul,
.list-section ol { margin: 0; padding-left: 22px; }
.list-section li { margin-bottom: 9px; line-height: 1.65; }
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 22px; }
.metric { padding: 13px; border-left: 3px solid #1f7a8c; background: #f4f8f9; }
.metric strong { display: block; margin-bottom: 3px; font-size: 21px; }
.metric span { color: #606266; font-size: 12px; }
.evidence-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 28px; }
.evidence-table h3 { margin: 0 0 8px; font-size: 14px; }
.data-row { justify-content: space-between; gap: 16px; padding: 8px 0; border-bottom: 1px solid #ebeef5; font-size: 13px; }
.data-row strong { white-space: nowrap; }
.muted { color: #909399; }
.report-footer { padding-top: 24px; color: #909399; font-size: 11px; text-align: center; }
.report-empty { padding-top: 80px; }
.history-filter { display: flex; gap: 10px; margin-bottom: 16px; }
.history-filter :deep(.el-date-editor) { flex: 1; min-width: 0; }
.history-filter-actions { display: flex; gap: 6px; }
.history-alert { margin-bottom: 14px; }
.history-list { border-top: 1px solid var(--border-color); }
.history-row {
  width: 100%;
  min-height: 88px;
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr) 20px;
  align-items: center;
  gap: 10px;
  padding: 13px 4px;
  border: 0;
  border-bottom: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-color);
  text-align: left;
  cursor: pointer;
}
.history-row:hover { background: var(--el-fill-color-light, #f5f7fa); }
.history-row:disabled { cursor: wait; opacity: 0.7; }
.history-row-icon { color: #1f7a8c; font-size: 18px; }
.history-row-content { min-width: 0; display: grid; gap: 5px; }
.history-row-content strong,
.history-row-content span,
.history-row-content small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.history-row-content strong { font-size: 14px; }
.history-row-content span { color: var(--text-secondary); font-size: 12px; }
.history-row-content small { color: #909399; font-size: 11px; }
.history-pagination { justify-content: center; margin-top: 18px; }

@media (max-width: 720px) {
  .page-header { align-items: flex-start; }
  .header-actions { flex-wrap: wrap; justify-content: flex-end; }
  .report-toolbar { align-items: stretch; flex-direction: column; }
  .report-toolbar :deep(.el-date-editor) { width: 100%; }
  .report-sheet { padding: 28px 20px 22px; }
  .report-heading h1 { font-size: 24px; }
  .two-column,
  .evidence-grid { grid-template-columns: 1fr; gap: 24px; }
  .metric-grid { grid-template-columns: repeat(2, 1fr); }
  .history-filter { align-items: stretch; flex-direction: column; }
  .history-filter :deep(.el-date-editor) { width: 100%; }
  .history-filter-actions { justify-content: flex-end; }
}

@media print {
  @page { size: A4; margin: 14mm; }
  .no-print { display: none !important; }
  .report-page { max-width: none; margin: 0; }
  .report-sheet { min-height: 0; padding: 0; border: 0; }
  .report-heading h1 { font-size: 25px; }
  .report-section { break-inside: avoid; }
  .evidence-section { break-before: page; }
  .metric { border: 1px solid #dcdfe6; border-left: 3px solid #1f4e5f; }
}
</style>
