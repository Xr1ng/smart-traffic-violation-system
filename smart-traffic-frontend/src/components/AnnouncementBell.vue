<template>
  <el-popover
    v-model:visible="popoverVisible"
    trigger="click"
    placement="bottom-end"
    :width="360"
    :popper-style="popoverStyle"
    @show="loadAnnouncements"
  >
    <template #reference>
      <el-tooltip content="系统公告" placement="bottom">
        <el-button
          class="announcement-trigger"
          text
          circle
          aria-label="系统公告"
        >
          <el-icon :size="20"><Bell /></el-icon>
        </el-button>
      </el-tooltip>
    </template>

    <div v-loading="loading" class="announcement-surface">
      <el-empty
        v-if="!loading && announcements.length === 0"
        description="暂无公告"
        :image-size="72"
      />
      <div v-else-if="!loading" class="announcement-list">
        <button
          v-for="announcement in announcements"
          :key="announcement.id"
          class="announcement-item"
          type="button"
          @click="openAnnouncement(announcement.id)"
        >
          <span class="announcement-item-title">{{ announcement.title }}</span>
          <time class="announcement-item-time" :datetime="announcement.updated_at">
            {{ formatDate(announcement.updated_at) }}
          </time>
        </button>
      </div>
    </div>
  </el-popover>

  <el-dialog
    v-model="detailVisible"
    class="announcement-dialog"
    width="min(640px, calc(100vw - 24px))"
    append-to-body
    destroy-on-close
  >
    <template #header>
      <div class="announcement-dialog-title">
        {{ selectedAnnouncement?.title || '系统公告' }}
      </div>
    </template>
    <div v-loading="detailLoading" class="announcement-detail">
      <div v-if="selectedAnnouncement" class="announcement-content">
        {{ selectedAnnouncement.content }}
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { fetchAnnouncement, fetchAnnouncements } from '@/api/announcement'

const popoverVisible = ref(false)
const loading = ref(false)
const announcements = ref([])
const detailVisible = ref(false)
const detailLoading = ref(false)
const selectedAnnouncement = ref(null)
const popoverStyle = {
  width: 'min(360px, calc(100vw - 24px))',
  maxWidth: 'calc(100vw - 24px)',
  padding: '12px'
}

async function loadAnnouncements() {
  loading.value = true
  try {
    const response = await fetchAnnouncements({ page: 1, page_size: 5 })
    announcements.value = response.data.items ?? []
  } catch {
    announcements.value = []
  } finally {
    loading.value = false
  }
}

async function openAnnouncement(id) {
  popoverVisible.value = false
  selectedAnnouncement.value = null
  detailVisible.value = true
  detailLoading.value = true
  try {
    const response = await fetchAnnouncement(id)
    selectedAnnouncement.value = response.data
  } catch {
    detailVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

function formatDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(value))
}
</script>

<style scoped>
.announcement-trigger {
  width: 32px;
  height: 32px;
  min-width: 32px;
  padding: 0;
  color: var(--text-secondary);
}

.announcement-trigger:hover,
.announcement-trigger:focus-visible {
  color: var(--text-color);
}

.announcement-surface {
  height: 300px;
  overflow: hidden;
}

.announcement-surface :deep(.el-empty) {
  height: 100%;
  padding: 0;
}

.announcement-list {
  height: 100%;
  overflow-y: auto;
}

.announcement-item {
  display: block;
  width: 100%;
  min-width: 0;
  padding: 12px 8px;
  border: 0;
  border-bottom: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-color);
  text-align: left;
  cursor: pointer;
}

.announcement-item:hover,
.announcement-item:focus-visible {
  background: var(--el-fill-color-light);
  outline: none;
}

.announcement-item-title {
  display: -webkit-box;
  overflow: hidden;
  font-size: 14px;
  line-height: 20px;
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.announcement-item-time {
  display: block;
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.announcement-dialog-title {
  padding-right: 32px;
  color: var(--text-color);
  font-size: 18px;
  font-weight: 600;
  line-height: 26px;
  overflow-wrap: anywhere;
}

.announcement-detail {
  min-height: 180px;
  max-height: min(60vh, 520px);
  overflow-y: auto;
}

.announcement-content {
  color: var(--text-color);
  font-size: 14px;
  line-height: 1.8;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

:global(.announcement-dialog .el-dialog__body) {
  padding-top: 8px;
}

@media (max-width: 480px) {
  .announcement-dialog-title {
    font-size: 16px;
    line-height: 24px;
  }
}
</style>
