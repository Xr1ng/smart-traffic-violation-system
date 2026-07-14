<template>
  <div class="header-right">
    <!-- 深色模式切换 -->
    <el-icon class="theme-toggle" :size="20" @click="themeStore.isDark = !themeStore.isDark">
      <Moon v-if="themeStore.isDark" />
      <Sunny v-else />
    </el-icon>

    <!-- 角色标签（可选） -->
    <el-tag v-if="roleLabel" size="small" type="danger">{{ roleLabel }}</el-tag>

    <!-- 用户下拉 -->
    <el-dropdown @command="handleCommand">
      <span class="user-info">
        {{ displayName }}
        <el-icon><ArrowDown /></el-icon>
      </span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="profile">
            <el-icon><User /></el-icon>个人信息
          </el-dropdown-item>
          <el-dropdown-item command="logout" divided>
            <el-icon><SwitchButton /></el-icon>退出登录
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { Moon, Sunny, ArrowDown, User, SwitchButton } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const props = defineProps({
  profilePath: { type: String, default: '/profile' },
  roleLabel: { type: String, default: '' },
  defaultName: { type: String, default: '用户' }
})

const router = useRouter()
const userStore = useUserStore()
const themeStore = useThemeStore()

const displayName = computed(() => userStore.userInfo?.username || props.defaultName)

function handleCommand(cmd) {
  if (cmd === 'profile') {
    router.push(props.profilePath).catch(() => {})
  } else if (cmd === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' }).then(() => {
      userStore.logout()
      router.push('/login')
    })
  }
}
</script>

<style scoped>
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.theme-toggle {
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.2s, transform 0.3s;
}
.theme-toggle:hover {
  color: var(--text-color);
  transform: rotate(30deg);
}
.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--text-color);
  white-space: nowrap;
}
</style>
