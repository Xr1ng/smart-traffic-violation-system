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

        <!-- 摘要 -->
        <el-alert :title="'报告摘要'" type="info" :closable="false" style="margin-bottom:20px">
          <p style="margin:8px 0;line-height:1.8">{{ currentReport.summary }}</p>
        </el-alert>

        <!-- 重点发现 -->
        <h4 style="margin:16px 0 12px">📌 重点发现</h4>
        <el-timeline>
          <el-timeline-item
            v-for="(h, i) in currentReport.highlights"
            :key="i"
            :timestamp="'发现 ' + (i + 1)"
            placement="top"
          >
            <el-card shadow="hover">
              <p>{{ h }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>

        <!-- 治理建议 -->
        <h4 style="margin:24px 0 12px">💡 治理建议</h4>
        <el-row :gutter="16">
          <el-col :span="12" v-for="(s, i) in currentReport.suggestions" :key="i">
            <el-card shadow="hover" style="margin-bottom:12px">
              <div class="suggestion-item">
                <el-tag type="primary" size="small" class="sug-num">{{ i + 1 }}</el-tag>
                <span>{{ s }}</span>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { generateReport } from '@/api/statistics'
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
    const res = await generateReport({
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
.suggestion-item { display: flex; align-items: flex-start; gap: 10px; line-height: 1.6; }
.sug-num { flex-shrink: 0; margin-top: 2px; }
</style>
