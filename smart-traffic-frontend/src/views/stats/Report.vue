<template>
  <div class="report-page">
    <div class="page-header">
      <h2 class="page-title">LLM 智能分析报告</h2>
      <el-button @click="router.back()">返回</el-button>
    </div>

    <!-- 报告生成 -->
    <el-card v-if="!currentReport" class="generate-card">
      <div class="generate-header">🤖 AI 智能分析报告生成</div>
      <el-form :model="genForm" label-width="100px" style="max-width:600px;margin-top:20px">
        <el-form-item label="时间范围">
          <el-radio-group v-model="genForm.dimension">
            <el-radio value="week">本周</el-radio>
            <el-radio value="month">本月</el-radio>
            <el-radio value="quarter">本季度</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="关注重点">
          <el-checkbox-group v-model="genForm.focus">
            <el-checkbox value="高发地点">高发地点</el-checkbox>
            <el-checkbox value="高发时段">高发时段</el-checkbox>
            <el-checkbox value="治理建议">治理建议</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="generating" @click="generateReport">
            <el-icon><MagicStick /></el-icon>生成报告
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 报告展示 -->
    <div v-else>
      <el-card>
        <template #header>
          <div class="report-title-row">
            <h3>{{ currentReport.title }}</h3>
            <el-button size="small" type="primary" @click="handleExport">导出 PDF</el-button>
          </div>
        </template>

        <div class="report-meta">
          <span>作者：{{ currentReport.author }}</span>
          <span>生成时间：{{ formatTime(currentReport.generated_at) }}</span>
        </div>
        <div class="report-content">{{ currentReport.content }}</div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { generateReport as generateReportApi } from '@/api/statistics'
import { ElMessage } from 'element-plus'

const router = useRouter()
const generating = ref(false)
const currentReport = ref(null)

const genForm = reactive({
  dimension: 'week',
  focus: ['高发地点', '高发时段', '治理建议']
})

async function generateReport() {
  generating.value = true
  try {
    const res = await generateReportApi({
      start_time: genForm.dimension === 'week' ? new Date(Date.now()-7*86400000).toISOString() : undefined,
      end_time: new Date().toISOString(), report_type: '综合' })
    currentReport.value = res.data
    ElMessage.success('报告已生成')
  } catch { ElMessage.error('生成失败') }
  generating.value = false
}

function handleExport() {
  ElMessage.success('正在导出 PDF...')
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : ''
}
</script>

<style scoped>
.report-page { }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { font-size: 20px; margin: 0; }
.generate-card { }
.generate-header { font-size: 18px; font-weight: 600; }
.report-title-row { display: flex; justify-content: space-between; align-items: center; }
.report-title-row h3 { margin: 0; }
.report-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  margin-bottom: 20px;
  color: var(--text-secondary);
  font-size: 13px;
}
.report-content { line-height: 1.8; white-space: pre-wrap; }
</style>
