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
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        class="sidebar-menu"
      >
        <!-- 数据概览 -->
        <el-menu-item index="/admin/stats" @click="nav('/admin/stats')">
          <el-icon><TrendCharts /></el-icon>
          <template #title>统计分析</template>
        </el-menu-item>

        <!-- 违章管理 -->
        <el-sub-menu index="violation-group">
          <template #title>
            <el-icon><WarningFilled /></el-icon>
            <span>违章管理</span>
          </template>
          <el-menu-item index="/admin/violations" @click="nav('/admin/violations')">违章列表</el-menu-item>
          <el-menu-item index="/admin/violations/upload" @click="nav('/admin/violations/upload')">违章上传</el-menu-item>
          <el-menu-item index="/review/workbench" @click="nav('/review/workbench')">案件审核</el-menu-item>
        </el-sub-menu>

        <!-- 车辆与驾驶人 -->
        <el-sub-menu index="vehicle-group">
          <template #title>
            <el-icon><Van /></el-icon>
            <span>车辆与驾驶人</span>
          </template>
          <el-menu-item index="/admin/vehicles" @click="nav('/admin/vehicles')">车辆管理</el-menu-item>
          <el-menu-item index="/admin/drivers" @click="nav('/admin/drivers')">驾驶人管理</el-menu-item>
        </el-sub-menu>

        <!-- 用户管理 -->
        <el-sub-menu index="user-group">
          <template #title>
            <el-icon><UserFilled /></el-icon>
            <span>用户管理</span>
          </template>
          <el-menu-item index="/admin/users" @click="nav('/admin/users')">用户列表</el-menu-item>
          <el-menu-item index="/admin/roles" @click="nav('/admin/roles')">角色权限</el-menu-item>
        </el-sub-menu>

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
          <el-menu-item index="/admin/sms-templates" @click="nav('/admin/sms-templates')">短信模板</el-menu-item>
          <el-menu-item index="/admin/announcements" @click="nav('/admin/announcements')">公告管理</el-menu-item>
        </el-sub-menu>

        <!-- 系统维护 -->
        <el-sub-menu index="system-group">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>系统维护</span>
          </template>
          <el-menu-item index="/admin/logs" @click="nav('/admin/logs')">操作日志</el-menu-item>
          <el-menu-item index="/admin/database" @click="nav('/admin/database')">数据库维护</el-menu-item>
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
        <div class="header-right">
          <el-icon class="theme-toggle" :size="20" @click="themeStore.isDark = !themeStore.isDark">
            <Moon v-if="themeStore.isDark" />
            <Sunny v-else />
          </el-icon>
          <el-tag size="small" type="danger">超级管理员</el-tag>
          <el-dropdown>
            <span class="user-info">
              {{ userStore.userInfo?.username || 'admin' }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/admin/profile')">个人信息</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main>
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

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()
const isCollapse = ref(false)

const activeMenu = computed(() => {
  const p = route.path
  if (p.startsWith('/review')) return '/review/workbench'
  return p
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
.el-main { background: var(--bg-color); padding: 20px; }
</style>
