<template>
  <div class="report-page">
    <div class="page-header">
      <h2 class="page-title">智能分析报告</h2>
      <el-button @click="router.back()">返回</el-button>
    </div>

    <el-result
      icon="info"
      title="AI 分析模块暂未接入"
      sub-title="当前仅提供现有统计数据，报告生成与导出暂不可用"
    />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { font-size: 20px; margin: 0; }
</style>
