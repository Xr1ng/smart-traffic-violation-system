<template>
  <div class="citizen-home">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header>📢 系统公告</template>
          <el-timeline v-if="announcements.length">
            <el-timeline-item v-for="item in announcements" :key="item.id" :timestamp="item.created_at" placement="top">
              <el-card shadow="hover">
                <h4>{{ item.title }}</h4>
                <p style="color:#666;margin-top:8px">{{ item.content }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <p v-else style="text-align:center;color:#999;padding:40px">暂无公告</p>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>🎯 快捷功能</template>
          <div class="quick-links">
            <div class="quick-link" @click="router.push('/citizen/report')">
              <el-icon :size="32" color="#e6a23c"><Camera /></el-icon>
              <span>随手拍举报</span>
            </div>
            <div class="quick-link" @click="router.push('/citizen/my-violations')">
              <el-icon :size="32" color="#f56c6c"><WarningFilled /></el-icon>
              <span>我的违章</span>
            </div>
            <div class="quick-link" @click="router.push('/citizen/my-reports')">
              <el-icon :size="32" color="#409eff"><List /></el-icon>
              <span>举报进度</span>
            </div>
            <div class="quick-link" @click="router.push('/citizen/vehicles')">
              <el-icon :size="32" color="#67c23a"><Van /></el-icon>
              <span>车辆绑定</span>
            </div>
          </div>
        </el-card>

        <el-card style="margin-top:16px">
          <template #header>ℹ️ 个人概览</template>
          <div class="overview-item">
            <span>我的违章</span>
            <span class="num">{{ stats.violations }}</span>
          </div>
          <div class="overview-item">
            <span>举报次数</span>
            <span class="num">{{ stats.reports }}</span>
          </div>
          <div class="overview-item">
            <span>获得奖励</span>
            <span class="num" style="color:#e6a23c">{{ stats.rewards }}元</span>
          </div>
          <div class="overview-item">
            <span>绑定车辆</span>
            <span class="num" style="color:#409eff">{{ stats.vehicles }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { fetchCases } from '@/api/case'
import { fetchOwnerViolations } from '@/api/violation'
import { getMyVehicles } from '@/api/vehicle'
import { useUserStore } from '@/stores/user'
import { summarizeCitizenOverview } from '@/utils/contracts'

const router = useRouter()
const userStore = useUserStore()
const announcements = ref([
  { id: 1, title: '系统升级通知', content: '系统将于 7 月 15 日进行升级维护，届时部分功能暂停使用。', created_at: '2026-07-05' }
])
const stats = reactive(summarizeCitizenOverview())

async function loadOverview() {
  const ownerId = userStore.userInfo?.id ?? JSON.parse(localStorage.getItem('userInfo') || '{}').id
  if (!ownerId) return

  try {
    const [violations, cases, vehicles] = await Promise.all([
      fetchOwnerViolations(ownerId),
      fetchCases({ source_type: 'citizen', page: 1, page_size: 100 }),
      getMyVehicles()
    ])
    Object.assign(stats, summarizeCitizenOverview(violations.data, cases.data, vehicles.data))
  } catch {}
}

onMounted(loadOverview)
</script>

<style scoped>
.quick-links {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 8px;
}
.quick-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 12px 14px;
  border-radius: 8px;
  transition: background .3s;
  font-size: 12px;
  min-width: 80px;
}
.quick-link:hover { background: var(--bg-color); }
.overview-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}
.overview-item .num { font-size: 20px; font-weight: bold; }
</style>
