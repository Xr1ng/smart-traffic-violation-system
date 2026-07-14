import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref<boolean>(localStorage.getItem('theme') === 'dark')

  function applyTheme(): void {
    const html = document.documentElement
    if (isDark.value) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  }

  // 切换时同步应用到 DOM
  watch(isDark, applyTheme)

  // 初始化时应用
  applyTheme()

  return { isDark }
})
