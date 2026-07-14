<template>
  <Transition name="btn-fade">
    <div v-show="visible" class="back-to-top" @click="scrollToTop">
      <el-icon :size="20"><ArrowUp /></el-icon>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ArrowUp } from '@element-plus/icons-vue'

const visible = ref(false)
let el = null

function onScroll() {
  visible.value = (el || document.documentElement).scrollTop > 400
}

function scrollToTop() {
  (el || document.documentElement).scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  // 查找最近的滚动容器（el-main）
  el = document.querySelector('.el-main')
  if (el) el.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('scroll', onScroll, { passive: true })
})

onUnmounted(() => {
  if (el) el.removeEventListener('scroll', onScroll)
  window.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.back-to-top {
  position: fixed;
  bottom: 40px;
  right: 40px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 999;
  transition: transform 0.2s, box-shadow 0.2s;
}
.back-to-top:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.btn-fade-enter-active,
.btn-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.btn-fade-enter-from,
.btn-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
