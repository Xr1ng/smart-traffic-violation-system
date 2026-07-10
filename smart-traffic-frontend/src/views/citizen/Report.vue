<template>
  <div class="page-container" style="max-width:800px">
    <div class="page-header">
      <h2 class="page-title">违章举报</h2>
    </div>

    <el-card>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="违章图片" prop="images">
          <el-upload
            :auto-upload="false"
            :on-change="handleImageChange"
            :before-remove="handleImageRemove"
            :file-list="fileList"
            list-type="picture-card"
            accept="image/*"
            :limit="3"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div style="color:#909399;font-size:12px;margin-top:4px">
            请拍摄清晰的违章现场照片，支持 jpg/png
          </div>
        </el-form-item>

        <el-form-item label="违章地点" prop="location">
          <el-input v-model="form.location" placeholder="请输入违章发生的具体地点" />
        </el-form-item>

        <el-form-item label="违章时间" prop="violation_time">
          <el-date-picker
            v-model="form.violation_time"
            type="datetime"
            placeholder="选择违章时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width:100%"
          />
        </el-form-item>

        <el-form-item label="违章描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请详细描述违章情况（如：车牌号、违章类型等）"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            提交举报
          </el-button>
          <el-button @click="router.push('/citizen/home')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { submitReport } from '@/api/violation'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)
const fileList = ref([])

const form = reactive({
  location: '', violation_time: '', description: ''
})

const rules = {
  location: [{ required: true, message: '请输入违章地点', trigger: 'blur' }],
  violation_time: [{ required: true, message: '请选择违章时间', trigger: 'change' }],
  description: [{ required: true, message: '请描述违章情况', trigger: 'blur' }]
}

function handleImageChange(file) {
  fileList.value.push(file)
}

function handleImageRemove(file) {
  const idx = fileList.value.indexOf(file)
  if (idx > -1) fileList.value.splice(idx, 1)
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (fileList.value.length === 0) {
    ElMessage.warning('请上传违章证据图片')
    return
  }
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('location_text', form.location)
    if (form.violation_time) fd.append('captured_at', form.violation_time)
    if (fileList.value.length > 0) fd.append('image', fileList.value[0].raw)

    await submitReport(fd)
    ElMessage.success('举报提交成功，请等待审核')
    router.push('/citizen/my-reports')
  } catch { /* handled */ }
  finally { submitting.value = false }
}
</script>
