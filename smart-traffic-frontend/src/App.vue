<template>
  <div class="error-boundary" v-if="hasError">
    <div class="error-box">
      <el-icon :size="48"><WarningFilled /></el-icon>
      <h2>页面发生异常</h2>
      <p>当前页面出现了一个意外错误，请尝试刷新页面。</p>
      <el-button type="primary" @click="reload">刷新页面</el-button>
      <p class="error-detail" v-if="errorMsg">{{ errorMsg }}</p>
    </div>
  </div>
  <router-view v-else />
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import { useUserStore } from '@/stores/user'
import { WarningFilled } from '@element-plus/icons-vue'

const userStore = useUserStore()
userStore.restoreLoginState()

const hasError = ref(false)
const errorMsg = ref('')

onErrorCaptured((err, instance, info) => {
  console.error('[ErrorBoundary]', err, info)
  hasError.value = true
  errorMsg.value = String(err)
  return false // 阻止向上冒泡
})

function reload() {
  window.location.reload()
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: var(--bg-color, #f5f5f5);
}
.error-box {
  text-align: center;
  padding: 40px;
  background: var(--el-bg-color, #fff);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  max-width: 480px;
}
.error-box h2 { margin: 16px 0 8px; font-size: 20px; color: var(--text-color, #303133); }
.error-box p { color: var(--text-secondary, #909399); margin-bottom: 20px; }
.error-detail { font-size: 12px; color: var(--el-color-danger, #f56c6c); word-break: break-all; margin-top: 16px; }
</style>
