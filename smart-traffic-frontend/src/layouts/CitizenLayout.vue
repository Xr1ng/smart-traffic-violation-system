<template>
  <el-container class="citizen-layout">
    <!-- 左侧侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar">
      <div class="sidebar-logo" @click="router.push('/citizen/home')">
        <h3 v-if="!isCollapse">🚦 交通违章</h3>
        <span v-else>🚦</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        :collapse="isCollapse"
        :collapse-transition="false"
      >
        <el-menu-item index="/citizen/home">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/citizen/my-violations">
          <el-icon><WarningFilled /></el-icon>
          <span>我的违章</span>
        </el-menu-item>
        <el-menu-item index="/citizen/report">
          <el-icon><Camera /></el-icon>
          <span>随手拍举报</span>
        </el-menu-item>
        <el-menu-item index="/citizen/my-reports">
          <el-icon><List /></el-icon>
          <span>举报进度</span>
        </el-menu-item>
        <el-menu-item index="/citizen/vehicles">
          <el-icon><Van /></el-icon>
          <span>车辆绑定</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶部 Header -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="toggle-btn" :size="20" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <span class="breadcrumb">市民服务平台</span>
        </div>
        <HeaderActions profile-path="/citizen/profile" default-name="用户" />
      </el-header>

      <el-main>
        <router-view v-slot="{ Component, route: r }">
          <Transition name="page-fade" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" :key="r.path" />
            </keep-alive>
          </Transition>
        </router-view>
        <BackToTop />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import HeaderActions from '@/components/HeaderActions.vue'
import BackToTop from '@/components/BackToTop.vue'
import {
  Fold, Expand, HomeFilled, WarningFilled, Camera, List, Van
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const isCollapse = ref(false)

const cachedViews = computed(() => {
  const names = []
  const collect = (routes) => {
    for (const r of routes) {
      if (r.children) collect(r.children)
      if (r.meta?.keepAlive && r.name) names.push(r.name)
    }
  }
  collect(router.options.routes)
  return names
})

const activeMenu = computed(() => route.path)

</script>

<style scoped>
.citizen-layout { min-height: 100vh; }
.sidebar {
  background: var(--header-bg);
  border-right: 1px solid var(--border-color);
  transition: width 0.3s;
  overflow: hidden;
}
.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
}
.sidebar-logo h3 {
  color: var(--text-color);
  font-size: 16px;
  margin: 0;
  white-space: nowrap;
}
.sidebar-menu {
  border-right: none !important;
  height: calc(100vh - 60px);
  overflow-y: auto;
}
.sidebar-menu .el-menu-item {
  height: 50px;
  line-height: 50px;
  font-size: 14px;
}
.sidebar-menu .el-menu-item:hover {
  background: var(--el-fill-color-light);
}
.sidebar-menu .el-menu-item.is-active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
  padding: 0 20px;
  height: 60px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.toggle-btn {
  cursor: pointer;
  color: var(--text-secondary);
}
.toggle-btn:hover { color: var(--text-color); }
.breadcrumb {
  font-size: 15px;
  color: var(--text-color);
}
.el-main {
  min-height: calc(100vh - 60px);
  background: var(--bg-color);
  padding: 16px;
  position: relative;
}
</style>
