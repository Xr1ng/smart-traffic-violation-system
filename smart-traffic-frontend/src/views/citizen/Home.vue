<template>
  <div class="citizen-home">
    <el-row :gutter="16">
      <!-- 左侧：宣传图片 + 系统公告 -->
      <el-col :span="12" :xs="24" :sm="24" :md="12">
        <!-- 宣传图片 -->
        <el-card class="banner-card" :body-style="{ padding: '0' }">
          <img src="/images/users.jpg" alt="交通安全宣传" class="banner-img" />
        </el-card>

        <!-- 系统公告 -->
        <el-card class="announcement-card" style="margin-top: 16px" :body-style="{ padding: '12px' }">
          <template #header>
            <div class="card-header">📢 系统公告</div>
          </template>
          <el-timeline v-if="announcements.length" class="compact-timeline">
            <el-timeline-item
              v-for="item in announcements"
              :key="item.id"
              :timestamp="item.created_at"
              placement="top"
            >
              <div class="announcement-title">{{ item.title }}</div>
              <div class="announcement-content">{{ item.content }}</div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无公告" :image-size="60" />
        </el-card>
      </el-col>

      <!-- 右侧：快捷功能 + 个人概览（缩小） -->
      <el-col :span="12" :xs="24" :sm="24" :md="12">
        <!-- 快捷功能 -->
        <el-card class="func-card" :body-style="{ padding: '16px' }">
          <template #header>
            <div class="card-header">🎯 快捷功能</div>
          </template>
          <div class="quick-links">
            <div class="quick-link" @click="router.push('/citizen/report')">
              <el-icon :size="28" color="#e6a23c"><Camera /></el-icon>
              <span>随手拍举报</span>
            </div>
            <div class="quick-link" @click="router.push('/citizen/my-violations')">
              <el-icon :size="28" color="#f56c6c"><WarningFilled /></el-icon>
              <span>我的违章</span>
            </div>
            <div class="quick-link" @click="router.push('/citizen/my-reports')">
              <el-icon :size="28" color="#409eff"><List /></el-icon>
              <span>举报进度</span>
            </div>
            <div class="quick-link" @click="router.push('/citizen/vehicles')">
              <el-icon :size="28" color="#67c23a"><Van /></el-icon>
              <span>车辆绑定</span>
            </div>
          </div>
        </el-card>

        <!-- 个人概览 -->
        <el-card class="overview-card" style="margin-top: 16px" :body-style="{ padding: '12px' }">
          <template #header>
            <div class="card-header">ℹ️ 个人概览</div>
          </template>
          <el-row :gutter="16">
            <el-col :span="6" :xs="12">
              <div class="stat-card">
                <div class="stat-label">我的违章</div>
                <div class="stat-num">{{ stats.violations }}</div>
              </div>
            </el-col>
            <el-col :span="6" :xs="12">
              <div class="stat-card">
                <div class="stat-label">举报次数</div>
                <div class="stat-num">{{ stats.reports }}</div>
              </div>
            </el-col>
            <el-col :span="6" :xs="12">
              <div class="stat-card">
                <div class="stat-label">获得奖励</div>
                <div class="stat-num" style="color:#e6a23c">{{ stats.rewards }}积分</div>
              </div>
            </el-col>
            <el-col :span="6" :xs="12">
              <div class="stat-card">
                <div class="stat-label">绑定车辆</div>
                <div class="stat-num" style="color:#409eff">{{ stats.vehicles }}</div>
              </div>
            </el-col>
          </el-row>
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
import { fetchAllCitizenCases, summarizeCitizenOverview } from '@/utils/contracts'

const router = useRouter()
const userStore = useUserStore()
const announcements = ref([])
const stats = reactive(summarizeCitizenOverview())

async function loadOverview() {
  const ownerId = userStore.userInfo?.id ?? JSON.parse(localStorage.getItem('userInfo') || '{}').id
  if (!ownerId) return

  try {
    const [violations, cases, vehicles] = await Promise.all([
      fetchOwnerViolations(ownerId),
      fetchAllCitizenCases(async params => {
        const res = await fetchCases(params)
        return res.data
      }),
      getMyVehicles()
    ])
    Object.assign(stats, summarizeCitizenOverview(violations.data, cases, vehicles.data))
  } catch {}
}

onMounted(loadOverview)
</script>

<style scoped>
.citizen-home { padding: 0; }
.card-header {
  font-weight: 600;
  font-size: 15px;
}
.announcement-card {
  min-height: 200px;
}
.announcement-card :deep(.el-card__header) {
  padding: 12px 16px;
}
.compact-timeline :deep(.el-timeline-item__node) {
  top: 4px;
}
.announcement-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-color);
  line-height: 1.4;
}
.announcement-content {
  font-size: 12px;
  color: #888;
  margin-top: 4px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.func-card :deep(.el-card__header) {
  padding: 12px 16px;
}
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
  padding: 12px 16px;
  border-radius: 8px;
  transition: background .3s;
  font-size: 13px;
  min-width: 80px;
}
.quick-link:hover { background: var(--el-fill-color-light); }

.overview-card :deep(.el-card__header) {
  padding: 12px 16px;
}
.stat-card {
  text-align: center;
  padding: 12px 8px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  transition: background .3s;
}
.stat-card:hover {
  background: var(--el-fill-color);
}
.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.stat-num {
  font-size: 22px;
  font-weight: bold;
  color: var(--text-color);
}

.banner-card { border-radius: 8px; overflow: hidden; }
.banner-img {
  display: block;
  width: 100%;
  height: auto;
  object-fit: contain;
}

@media (max-width: 768px) {
  .el-col { margin-bottom: 12px; }
  .el-col:last-child { margin-bottom: 0; }
  .banner-img { height: 160px; }
}
</style>
