<template>
  <el-container class="admin-layout">
    <!-- 左侧侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo" @click="router.push('/admin/stats')">
        <span v-if="!isCollapse">🚦 交通违章管理</span>
        <span v-else>🚦</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        background-color="transparent"
        text-color="#C8DDE4"
        active-text-color="#A2D9F0"
        class="sidebar-menu"
      >
        <!-- 违章管理 -->
        <el-sub-menu index="violation-group">
          <template #title>
            <el-icon><WarningFilled /></el-icon>
            <span>违章管理</span>
          </template>
          <el-menu-item index="/admin/violations/upload" @click="nav('/admin/violations/upload')">证据上传</el-menu-item>
          <el-menu-item index="/admin/violations/review" @click="nav('/admin/violations/review')">案件审核</el-menu-item>
          <el-menu-item index="/admin/violations" @click="nav('/admin/violations')">违章列表</el-menu-item>
          <el-menu-item index="/admin/stats" @click="nav('/admin/stats')">统计分析</el-menu-item>
        </el-sub-menu>

        <!-- 车辆管理 -->
        <el-menu-item index="/admin/vehicles" @click="nav('/admin/vehicles')">
          <el-icon><Van /></el-icon>
          <template #title>车辆管理</template>
        </el-menu-item>

        <!-- 用户管理 -->
        <el-menu-item index="/admin/users" @click="nav('/admin/users')">
          <el-icon><UserFilled /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>

        <!-- 设备管理 -->
        <el-menu-item index="/admin/cameras" @click="nav('/admin/cameras')">
          <el-icon><VideoCamera /></el-icon>
          <template #title>摄像头管理</template>
        </el-menu-item>

        <!-- 系统配置 -->
        <el-sub-menu index="config-group">
          <template #title>
            <el-icon><Tools /></el-icon>
            <span>系统配置</span>
          </template>
          <el-menu-item index="/admin/rules" @click="nav('/admin/rules')">违章规则</el-menu-item>
          <el-menu-item index="/admin/announcements" @click="nav('/admin/announcements')">公告管理</el-menu-item>
        </el-sub-menu>

        <!-- 系统维护 -->
        <el-sub-menu index="system-group">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>系统维护</span>
          </template>
          <el-menu-item index="/admin/logs" @click="nav('/admin/logs')">操作日志</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" /><Expand v-else />
          </el-icon>
          <span class="page-name">{{ route.meta.title }}</span>
        </div>
        <HeaderActions profile-path="/admin/profile" role-label="超级管理员" default-name="admin" />
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
  WarningFilled, Van, UserFilled, VideoCamera, Tools, Monitor, Fold, Expand
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const isCollapse = ref(false)

// keep-alive 白名单从路由 meta 读取
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

function nav(path) {
  if (route.path !== path) router.push(path).catch(() => {})
}
</script>

<style scoped>
.admin-layout { height: 100vh; }
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
  font-size: 18px;
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
.sidebar-menu .el-sub-menu .el-menu-item {
  height: 44px;
  line-height: 44px;
  min-width: auto;
}
.sidebar-menu .el-menu-item:hover,
.sidebar-menu .el-sub-menu__title:hover {
  background: rgba(255, 255, 255, 0.08) !important;
}
.sidebar-menu .el-menu-item.is-active {
  background: rgba(162, 217, 240, 0.15) !important;
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
.el-main {
  background: var(--bg-color);
  padding: 20px;
  position: relative;
}
</style>
