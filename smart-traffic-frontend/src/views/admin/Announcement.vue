<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">公告管理</h2>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新增公告
      </el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column prop="content" label="正文" min-width="320" show-overflow-tooltip />
      <el-table-column label="更新时间" width="180">
        <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">
            <el-icon><Edit /></el-icon>编辑
          </el-button>
          <el-button
            size="small"
            type="danger"
            :loading="deletingId === row.id"
            @click="removeAnnouncement(row)"
          >
            <el-icon><Delete /></el-icon>删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadList"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑公告' : '新增公告'" width="min(560px, 92vw)">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="正文" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="8"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveAnnouncement">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Edit, Plus } from '@element-plus/icons-vue'
import {
  createAnnouncement,
  deleteAnnouncement,
  fetchAnnouncements,
  updateAnnouncement
} from '@/api/announcement'
import { buildAnnouncementPayload } from '@/utils/contracts'

const list = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const deletingId = ref(null)
const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const form = reactive({ title: '', content: '' })

const rules = {
  title: [
    { required: true, message: '请输入公告标题', trigger: 'blur' },
    { max: 100, message: '标题不能超过 100 个字符', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入公告正文', trigger: 'blur' },
    { max: 5000, message: '正文不能超过 5000 个字符', trigger: 'blur' }
  ]
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : ''
}

async function loadList() {
  loading.value = true
  try {
    const response = await fetchAnnouncements({ page: page.value, page_size: pageSize.value })
    list.value = response.data.items
    total.value = response.data.total
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}

function resetForm(data = {}) {
  Object.assign(form, {
    title: data.title ?? '',
    content: data.content ?? ''
  })
  nextTick(() => formRef.value?.clearValidate())
}

function openCreate() {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  resetForm(row)
  dialogVisible.value = true
}

async function saveAnnouncement() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = buildAnnouncementPayload(form)
    if (editingId.value) {
      await updateAnnouncement(editingId.value, payload)
      ElMessage.success('公告已更新')
    } else {
      await createAnnouncement(payload)
      ElMessage.success('公告已创建')
    }
    dialogVisible.value = false
    await loadList()
  } catch { /* keep the form open for correction or retry */ }
  finally { saving.value = false }
}

async function removeAnnouncement(row) {
  try {
    await ElMessageBox.confirm(`确定删除公告“${row.title}”吗？`, '删除公告', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    deletingId.value = row.id
    await deleteAnnouncement(row.id)
    if (list.value.length === 1 && page.value > 1) page.value -= 1
    await loadList()
    ElMessage.success('公告已删除')
  } catch (error) {
    if (!['cancel', 'close'].includes(error)) {
      // Request failures are already surfaced by the shared interceptor.
    }
  } finally {
    deletingId.value = null
  }
}

onMounted(loadList)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-title { margin: 0; font-size: 20px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
