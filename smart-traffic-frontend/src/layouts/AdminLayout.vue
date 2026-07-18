<template>
  <el-container class="app-layout admin-layout">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">
      <button type="button" class="brand" @click="nav('/admin/stats')">
        <el-icon :size="22"><LocationFilled /></el-icon>
        <span v-if="!isCollapse">智能交通管理</span>
      </button>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        class="sidebar-menu"
      >
        <el-sub-menu index="violations">
          <template #title>
            <el-icon><WarningFilled /></el-icon>
            <span>违章管理</span>
          </template>
          <el-menu-item index="/admin/violations/upload" @click="nav('/admin/violations/upload')">证据上传</el-menu-item>
          <el-menu-item index="/admin/violations/review" @click="nav('/admin/violations/review')">案件审核</el-menu-item>
          <el-menu-item index="/admin/violations" @click="nav('/admin/violations')">违章列表</el-menu-item>
          <el-menu-item index="/admin/stats" @click="nav('/admin/stats')">统计分析</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/admin/vehicles" @click="nav('/admin/vehicles')">
          <el-icon><Van /></el-icon>
          <template #title>车辆管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/users" @click="nav('/admin/users')">
          <el-icon><UserFilled /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/cameras" @click="nav('/admin/cameras')">
          <el-icon><VideoCamera /></el-icon>
          <template #title>设备管理</template>
        </el-menu-item>

        <el-menu-item index="/admin/announcements" @click="nav('/admin/announcements')">
          <el-icon><Bell /></el-icon>
          <template #title>公告管理</template>
        </el-menu-item>

        <el-menu-item index="/admin/logs" @click="nav('/admin/logs')">
          <el-icon><Document /></el-icon>
          <template #title>系统日志</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="layout-body">
      <el-header class="app-header">
        <div class="header-context">
          <el-tooltip :content="isCollapse ? '展开菜单' : '收起菜单'" placement="bottom">
            <el-button text circle aria-label="切换侧边栏" @click="isCollapse = !isCollapse">
              <el-icon :size="20"><Expand v-if="isCollapse" /><Fold v-else /></el-icon>
            </el-button>
          </el-tooltip>
          <el-breadcrumb separator="/" class="breadcrumbs">
            <el-breadcrumb-item
              v-for="item in breadcrumbItems"
              :key="`${item.label}-${item.path}`"
              :to="item.path || undefined"
            >
              {{ item.label }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <HeaderActions
          profile-path="/admin/profile"
          role-label="超级管理员"
          role-tag-type="danger"
          default-name="管理员"
        />
      </el-header>

      <el-main ref="mainRef" class="app-main">
        <router-view v-slot="{ Component, route: viewRoute }">
          <KeepAlive>
            <component
              :is="Component"
              v-if="viewRoute.meta.keepAlive"
              :key="viewRoute.name"
            />
          </KeepAlive>
          <component
            :is="Component"
            v-if="!viewRoute.meta.keepAlive"
            :key="viewRoute.fullPath"
          />
        </router-view>
        <BackToTop :target="mainElement" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Bell, Document, Expand, Fold, LocationFilled,
  UserFilled, Van, VideoCamera, WarningFilled
} from '@element-plus/icons-vue'
import BackToTop from '@/components/BackToTop.vue'
import HeaderActions from '@/components/HeaderActions.vue'
import { useResponsiveSidebar } from '@/composables/useResponsiveSidebar'

const router = useRouter()
const route = useRoute()
const { isCollapse } = useResponsiveSidebar()
const mainRef = ref(null)
const mainElement = computed(() => mainRef.value?.$el || mainRef.value)

const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/violations/')) {
    if (route.path === '/admin/violations/upload') return route.path
    if (route.path === '/admin/violations/review') return route.path
    return '/admin/violations'
  }
  return route.path
})

const parentLabels = [
  [/^\/admin\/violations/, '违章管理']
]

const breadcrumbItems = computed(() => {
  const items = [{ label: '管理后台', path: '/admin/stats' }]
  const parent = parentLabels.find(([pattern]) => pattern.test(route.path))
  if (parent) items.push({ label: parent[1], path: '' })
  const title = route.meta.title
  if (title && title !== items.at(-1).label && route.path !== '/admin/stats') {
    items.push({ label: title, path: '' })
  }
  return items
})

function nav(path) {
  if (route.path !== path) router.push(path)
}
</script>

<style scoped>
.app-layout { height: 100vh; min-width: 0; }
.app-aside { display: flex; flex-direction: column; overflow: hidden; background: var(--sidebar-bg); transition: width 0.2s; }
.brand { display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; height: 60px; flex: 0 0 60px; padding: 0 10px; color: #fff; font: inherit; font-weight: 600; background: transparent; border: 0; cursor: pointer; white-space: nowrap; }
.sidebar-menu { flex: 1; overflow-y: auto; border-right: 0; background: transparent; }
.sidebar-menu :deep(.el-menu-item), .sidebar-menu :deep(.el-sub-menu__title) { color: #c8d1d8; }
.sidebar-menu :deep(.el-menu-item:hover), .sidebar-menu :deep(.el-sub-menu__title:hover) { background: rgba(255,255,255,0.08); }
.sidebar-menu :deep(.el-menu-item.is-active) { color: #fff; background: rgba(64,158,255,0.24); }
.sidebar-menu :deep(.el-sub-menu .el-menu) { background: transparent; }
.sidebar-menu :deep(.el-sub-menu .el-menu .el-menu-item) { background: transparent; }
.layout-body { min-width: 0; }
.app-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; height: 60px; padding: 0 20px; background: var(--header-bg); border-bottom: 1px solid var(--border-color); }
.header-context { display: flex; align-items: center; min-width: 0; gap: 10px; }
.breadcrumbs { min-width: 0; }
.breadcrumbs :deep(.el-breadcrumb__inner) { color: var(--text-secondary); }
.breadcrumbs :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) { color: var(--text-color); font-weight: 600; }
.app-main { position: relative; min-width: 0; padding: 20px; overflow: auto; background: var(--bg-color); }
@media (max-width: 720px) { .app-header { padding: 0 10px; } .breadcrumbs { display: none; } .app-main { padding: 12px; } }
</style>
