<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">公告管理</h2>
      <el-button type="primary" @click="openCreate">新增公告</el-button>
    </div>

    <el-card>
      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="title" label="公告标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="content" label="公告内容" min-width="300" show-overflow-tooltip />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_published ? 'success' : 'info'" size="small">
              {{ row.is_published ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editItem(row)">编辑</el-button>
            <el-button
              size="small"
              :type="row.is_published ? 'warning' : 'success'"
              @click="togglePublish(row)"
            >
              {{ row.is_published ? '下架' : '发布' }}
            </el-button>
            <el-popconfirm title="确定删除此公告?" @confirm="deleteItem(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && list.length === 0" description="暂无公告，点击新增创建第一条公告" />
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑公告' : '新增公告'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="公告标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入公告标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="公告内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            placeholder="请输入公告内容"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.is_published">
            <el-radio :value="true">发布</el-radio>
            <el-radio :value="false">存为草稿</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchAnnouncements,
  createAnnouncement,
  updateAnnouncement,
  deleteAnnouncement
} from '@/utils/announcements'

const list = ref([])
const loading = ref(false)
const formRef = ref(null)
const dialog = reactive({ visible: false, isEdit: false, editId: null })
const form = reactive({ title: '', content: '', is_published: true })
const rules = {
  title: [{ required: true, message: '请输入公告标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入公告内容', trigger: 'blur' }]
}

function loadList() {
  loading.value = true
  // 模拟异步体验
  setTimeout(() => {
    list.value = fetchAnnouncements()
    loading.value = false
  }, 200)
}

function resetForm() {
  Object.assign(form, { title: '', content: '', is_published: true })
  formRef.value?.clearValidate()
}

function openCreate() {
  dialog.isEdit = false
  dialog.editId = null
  resetForm()
  dialog.visible = true
}

function editItem(row) {
  dialog.isEdit = true
  dialog.editId = row.id
  Object.assign(form, {
    title: row.title,
    content: row.content,
    is_published: row.is_published
  })
  formRef.value?.clearValidate()
  dialog.visible = true
}

async function save() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  if (dialog.isEdit) {
    updateAnnouncement(dialog.editId, {
      title: form.title,
      content: form.content,
      is_published: form.is_published
    })
    ElMessage.success('公告更新成功')
  } else {
    createAnnouncement({
      title: form.title,
      content: form.content,
      is_published: form.is_published
    })
    ElMessage.success('公告创建成功')
  }
  dialog.visible = false
  loadList()
}

function togglePublish(row) {
  const newStatus = !row.is_published
  updateAnnouncement(row.id, { is_published: newStatus })
  ElMessage.success(newStatus ? '公告已发布' : '公告已下架')
  loadList()
}

function deleteItem(id) {
  deleteAnnouncement(id)
  ElMessage.success('公告已删除')
  loadList()
}

onMounted(loadList)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { font-size: 20px; margin: 0; }
</style>
