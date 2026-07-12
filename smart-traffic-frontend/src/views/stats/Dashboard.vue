<template>
  <div class="stats-dashboard">
    <div class="page-header">
      <h2 class="page-title">统计分析台</h2>
      <div class="header-actions">
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" size="small" style="width:220px" @change="loadData" />
        <el-button-group>
          <el-button :type="period === '7d' ? 'primary' : ''" size="small" @click="setPeriod('7d')">近7天</el-button>
          <el-button :type="period === '30d' ? 'primary' : ''" size="small" @click="setPeriod('30d')">近30天</el-button>
        </el-button-group>
        <el-button type="primary" size="small" @click="router.push(reportPathForRoute(route.path))">
          <el-icon><Document /></el-icon>生成报告
        </el-button>
      </div>
    </div>

    <!-- 概览指标卡片 -->
    <el-row :gutter="10" class="overview-row">
      <el-col :xs="12" :sm="8" :md="4" v-for="card in overviewCards" :key="card.label">
        <el-card shadow="hover" class="stat-card" :body-style="{ padding: '10px 6px' }">
          <div class="stat-icon" :style="{ background: card.bg }">
            <el-icon :size="16"><component :is="card.icon" /></el-icon>
          </div>
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表行：违章趋势 + 违章类型占比 + 区域排行 -->
    <el-row :gutter="12" style="margin-top:10px">
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header><span>📈 违章趋势</span></template>
          <div ref="trendChart" style="width:100%;height:260px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header><span>🎯 违章类型占比</span></template>
          <div ref="typeChart" style="width:100%;height:260px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header><span>📍 区域排行</span></template>
          <div ref="regionChart" style="width:100%;height:260px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 路段‑时段热力图 -->
    <el-row :gutter="12" style="margin-top:10px">
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header><span>🔥 路段‑时段热力图</span></template>
          <div ref="heatmapChart" style="width:100%;height:340px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchOverview, fetchByTime, fetchByType, fetchByLocation, fetchRoadTimeHeatmap } from '@/api/statistics'
import { mapNamedSeries, reportPathForRoute } from '@/utils/contracts'
import * as echarts from 'echarts'
import { WarningFilled, TrendCharts, List, DataAnalysis, Checked, Collection, Document } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const dateRange = ref([])
const period = ref('30d')

const trendChart = ref(null)
const typeChart = ref(null)
const regionChart = ref(null)
const heatmapChart = ref(null)

const overview = ref({})
const trend = ref([])
const typeRatio = ref([])
const regionRank = ref([])
const heatmapData = ref({ time_slots: [], roads: [], items: [] })

const chartInstances = []

function setPeriod(p) {
  period.value = p
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - (p === '7d' ? 6 : 29))
  dateRange.value = [start, end]
  loadData()
}

const overviewCards = computed(() => {
  const d = overview.value
  return [
    { label: '总违章数', value: d.total_violations ?? 0, color: '#409eff', bg: 'rgba(64,158,255,0.1)', icon: 'WarningFilled' },
    { label: '今日新增', value: d.today_new ?? 0, color: '#67c23a', bg: 'rgba(103,194,58,0.1)', icon: 'TrendCharts' },
    { label: '待审核', value: d.pending_count ?? 0, color: '#e6a23c', bg: 'rgba(230,162,60,0.1)', icon: 'List' },
    { label: '通过率', value: `${d.approve_rate ?? 0}%`, color: '#409eff', bg: 'rgba(64,158,255,0.1)', icon: 'Checked' },
    { label: '驳回率', value: `${d.reject_rate ?? 0}%`, color: '#f56c6c', bg: 'rgba(245,108,108,0.1)', icon: 'DataAnalysis' },
    { label: '通知成功率', value: `${d.notify_success_rate ?? 0}%`, color: '#67c23a', bg: 'rgba(103,194,58,0.1)', icon: 'Collection' }
  ]
})

async function loadData() {
  const params = {}
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_time = dateRange.value[0]
    params.end_time = dateRange.value[1]
  }
  try {
    const [ov, tr, ty, rg] = await Promise.all([
      fetchOverview(params).catch(() => ({ data: {} })),
      fetchByTime(params).catch(() => ({ data: { items: [] } })),
      fetchByType(params).catch(() => ({ data: { items: [] } })),
      fetchByLocation(params).catch(() => ({ data: { items: [] } }))
    ])
    overview.value = ov.data || ov
    trend.value = (tr.data?.items || []).map(t => ({ date: t.date, count: t.count }))
    typeRatio.value = mapNamedSeries(ty.data || ty)
    regionRank.value = mapNamedSeries(rg.data || rg)
    const hm = await fetchRoadTimeHeatmap(params).catch(() => ({ data: { time_slots: [], roads: [], items: [] } }))
    heatmapData.value = hm.data || hm
  } catch (e) {
    console.error('加载统计数据失败:', e)
  }
  await nextTick()
  renderAll()
}

function renderAll() {
  renderTrend()
  renderType()
  renderRegion()
  renderHeatmap()
}

function getOrInit(refEl) {
  if (!refEl) return null
  const instance = echarts.getInstanceByDom(refEl) || echarts.init(refEl)
  if (!chartInstances.includes(instance)) chartInstances.push(instance)
  return instance
}

function renderTrend() {
  const chart = getOrInit(trendChart.value)
  if (!chart) return
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 8, right: 8, bottom: 30, top: 8, containLabel: true },
    xAxis: { type: 'category', data: trend.value.map(t => t.date?.slice(5)), axisLabel: { rotate: 45, fontSize: 10 }, axisTick: { alignWithLabel: true } },
    yAxis: { type: 'value', name: '件', splitLine: { lineStyle: { type: 'dashed', color: '#e0e0e0' } } },
    series: [{
      data: trend.value.map(t => t.count),
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 5,
      lineStyle: { width: 2.5, color: '#409eff' },
      itemStyle: { color: '#409eff' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(64,158,255,0.3)' },
        { offset: 1, color: 'rgba(64,158,255,0.02)' }
      ]) }
    }]
  })
}

function renderType() {
  const chart = getOrInit(typeChart.value)
  if (!chart) return
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
    legend: { bottom: 0, textStyle: { fontSize: 11 }, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie',
      radius: ['42%', '70%'],
      center: ['50%', '42%'],
      roseType: 'area',
      data: typeRatio.value,
      label: { show: true, formatter: '{b}\n{d}%', fontSize: 10 },
      color: ['#f56c6c', '#e6a23c', '#409eff', '#67c23a', '#909399', '#b37feb']
    }]
  })
}

function renderRegion() {
  const chart = getOrInit(regionChart.value)
  if (!chart) return
  const data = [...regionRank.value].reverse()
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 5, right: 40, bottom: 5, top: 5, containLabel: true },
    xAxis: { type: 'value', name: '件' },
    yAxis: { type: 'category', data: data.map(r => r.name), inverse: true, axisLabel: { fontSize: 11 } },
    series: [{
      data: data.map((r, i) => {
        const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#9b59b6', '#17a2b8']
        return { value: r.value, itemStyle: { color: colors[i % colors.length], borderRadius: [0, 4, 4, 0] } }
      }),
      type: 'bar',
      barMaxWidth: 28,
      label: { show: true, position: 'right', fontSize: 11 }
    }]
  })
}

function renderHeatmap() {
  const chart = getOrInit(heatmapChart.value)
  if (!chart) return
  const { time_slots: slots, roads, items } = heatmapData.value
  if (!roads.length || !items.length) {
    chart.setOption({
      title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999', fontSize: 14 } },
      xAxis: { show: false }, yAxis: { show: false }, series: []
    })
    return
  }
  const slotIndex = {}
  slots.forEach((s, i) => { slotIndex[s] = i })
  const roadIndex = {}
  roads.forEach((r, i) => { roadIndex[r] = i })

  const data = []
  const maxCount = items.reduce((mx, it) => Math.max(mx, it.count), 0) || 1
  items.forEach(it => {
    const x = slotIndex[it.time_slot]
    const y = roadIndex[it.road]
    if (x !== undefined && y !== undefined) {
      data.push([x, y, it.count])
    }
  })

  chart.setOption({
    tooltip: {
      position: 'top',
      formatter: p => `${roads[p.value[1]]} · ${slots[p.value[0]]}时<br/>违章数: <b>${p.value[2]}</b> 件`
    },
    grid: { left: 120, right: 30, bottom: 40, top: 10 },
    xAxis: {
      type: 'category', data: slots, splitArea: { show: true },
      axisLabel: { rotate: 45, fontSize: 11 }
    },
    yAxis: {
      type: 'category', data: roads, splitArea: { show: true },
      axisLabel: { fontSize: 11 }
    },
    visualMap: {
      min: 0, max: maxCount,
      calculable: true,
      orient: 'horizontal',
      left: 'center', bottom: 0,
      inRange: { color: ['#f0f9ff', '#bae6fd', '#7dd3fc', '#38bdf8', '#0ea5e9', '#0284c7', '#0369a1'] },
      textStyle: { fontSize: 11 }
    },
    series: [{
      type: 'heatmap', data,
      label: { show: data.length < 50, fontSize: 11 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' } }
    }]
  })
}

function handleResize() {
  chartInstances.forEach(c => c.resize())
}

onMounted(async () => {
  await loadData()
  await nextTick()
  renderAll()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstances.forEach(c => c.dispose())
})
</script>

<style scoped>
.stats-dashboard { }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}
.page-title { font-size: 20px; margin: 0; font-weight: 600; }
.header-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }

.overview-row { margin-bottom: 0; }
.stat-card {
  text-align: center;
  cursor: default;
  transition: transform 0.2s;
}
.stat-card:hover { transform: translateY(-2px); }
.stat-icon {
  width: 34px; height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 4px;
}
.stat-value { font-size: 22px; font-weight: bold; margin-bottom: 2px; }
.stat-label { font-size: 11px; color: #909399; }

.chart-card {
  height: 100%;
}
.chart-card :deep(.el-card__header) {
  padding: 8px 12px;
  font-weight: 500;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.chart-card :deep(.el-card__body) {
  padding: 8px;
}
</style>
