<template>
  <el-container class="review-layout">
    <!-- 左侧侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo" @click="router.push('/review/workbench')">
        <span v-if="!isCollapse">🚦 交管审核平台</span>
        <span v-else>🚦</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        background-color="transparent"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        class="sidebar-menu"
      >
        <el-menu-item index="/review/workbench" @click="nav('/review/workbench')">
          <el-icon><Checked /></el-icon>
          <template #title>案件审核</template>
        </el-menu-item>

        <el-menu-item index="/review/violations" @click="nav('/review/violations')">
          <el-icon><List /></el-icon>
          <template #title>违章记录</template>
        </el-menu-item>

        <el-menu-item index="/review/upload" @click="nav('/review/upload')">
          <el-icon><Upload /></el-icon>
          <template #title>证据上传</template>
        </el-menu-item>

        <el-menu-item index="/stats" @click="nav('/stats')">
          <el-icon><TrendCharts /></el-icon>
          <template #title>统计分析</template>
        </el-menu-item>

        <el-menu-item v-if="userStore.role === 'admin'" index="/admin/users" @click="nav('/admin/users')">
          <el-icon><Setting /></el-icon>
          <template #title>系统管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧主内容 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" /><Expand v-else />
          </el-icon>
          <span class="page-name">{{ route.meta.title }}</span>
        </div>
        <div class="header-right">
          <AnnouncementBell />
          <el-icon class="theme-toggle" :size="20" @click="themeStore.isDark = !themeStore.isDark">
            <Moon v-if="themeStore.isDark" />
            <Sunny v-else />
          </el-icon>
          <el-dropdown>
            <span class="user-info">
              {{ userStore.userInfo?.username || '工作人员' }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/review/profile')">
                  <el-icon><User /></el-icon>个人信息
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import AnnouncementBell from '@/components/AnnouncementBell.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()
const isCollapse = ref(false)

const activeMenu = computed(() => {
  const p = route.path
  if (p.startsWith('/stats')) return '/stats'
  if (p.startsWith('/review')) return '/' + p.split('/').slice(0, 2).join('/')
  return '/review/workbench'
})

function nav(path) {
  if (route.path !== path) router.push(path).catch(() => {})
}

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' }).then(() => {
    userStore.logout()
    router.push('/login')
  })
}
</script>

<style scoped>
.review-layout { height: 100vh; }
.aside {
  background: var(--sidebar-bg);
  overflow: hidden;
  transition: width 0.3s;
  display: flex;
  flex-direction: column;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 17px;
  font-weight: bold;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}
.sidebar-menu {
  border-right: none !important;
  flex: 1;
  overflow-y: auto;
}
.sidebar-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
}
.sidebar-menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.08) !important;
}
.sidebar-menu .el-menu-item.is-active {
  background: rgba(64, 158, 255, 0.12) !important;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
  padding: 0 20px;
  height: 60px;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.collapse-btn { font-size: 20px; cursor: pointer; }
.page-name { font-size: 16px; font-weight: 500; }
.header-right { display: flex; align-items: center; gap: 16px; }
.user-info { cursor: pointer; display: flex; align-items: center; gap: 4px; }
.theme-toggle { cursor: pointer; color: var(--text-secondary); }
.theme-toggle:hover { color: var(--text-color); }
.main-content {
  background: var(--bg-color);
  padding: 20px;
  overflow-y: auto;
}
</style>
