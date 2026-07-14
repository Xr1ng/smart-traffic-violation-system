<template>
  <div class="page-container" style="max-width:800px">
    <div class="page-header">
      <h2 class="page-title">违章举报</h2>
    </div>

    <el-card>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="违法类型" prop="reported_violation_type">
          <el-radio-group v-model="form.reported_violation_type">
            <el-radio-button value="illegal_stop">违停</el-radio-button>
            <el-radio-button value="red_light_violation">疑似闯红灯</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="违章图片" prop="images">
          <div class="upload-area">
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              style="display:none"
              @change="onFilePicked"
            />
            <div class="upload-card" @click="openFilePicker">
              <el-icon :size="28"><Plus /></el-icon>
              <span>点击上传</span>
            </div>
            <div
              v-for="(preview, idx) in previews"
              :key="idx"
              class="upload-card preview-card"
              @click="removePreview(idx)"
            >
              <img :src="preview" alt="preview" />
              <div class="preview-overlay">
                <el-icon><Delete /></el-icon>
              </div>
            </div>
          </div>
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
import { citizenReport } from '@/api/intake'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref(null)
const fileInputRef = ref(null)
const submitting = ref(false)
const selectedFiles = ref([])       // 原始 File 对象
const previews = ref([])            // data: URL 预览

const form = reactive({
  reported_violation_type: '', location: '', violation_time: '', description: ''
})

const rules = {
  reported_violation_type: [{ required: true, message: '请选择违法类型', trigger: 'change' }],
  location: [{ required: true, message: '请输入违章地点', trigger: 'blur' }],
  violation_time: [{ required: true, message: '请选择违章时间', trigger: 'change' }],
  description: [{ required: true, message: '请描述违章情况', trigger: 'blur' }]
}

function openFilePicker() {
  if (selectedFiles.value.length >= 3) {
    ElMessage.warning('最多上传 3 张图片')
    return
  }
  fileInputRef.value?.click()
}

function onFilePicked(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    return
  }
  selectedFiles.value.push(file)
  const reader = new FileReader()
  reader.onload = () => {
    previews.value.push(reader.result)
  }
  reader.readAsDataURL(file)
  // 重置 input 以便重复选择同一文件
  e.target.value = ''
}

function removePreview(idx) {
  selectedFiles.value.splice(idx, 1)
  previews.value.splice(idx, 1)
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请上传违章证据图片')
    return
  }
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('reported_violation_type', form.reported_violation_type)
    fd.append('location_text', form.location)
    fd.append('captured_at', form.violation_time)
    if (form.description) fd.append('description', form.description)
    fd.append('image', selectedFiles.value[0])
    await citizenReport(fd)
    ElMessage.success('举报提交成功，请等待审核')
    router.push('/citizen/my-reports')
  } catch { /* handled */ }
  finally { submitting.value = false }
}
</script>

<style scoped>
.upload-area {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.upload-card {
  width: 148px;
  height: 148px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #8c939d;
  font-size: 12px;
  cursor: pointer;
  transition: border-color .3s;
  background: #fafafa;
}
.upload-card:hover {
  border-color: #72a8c4;
  color: #72a8c4;
}
.preview-card {
  position: relative;
  border-style: solid;
  overflow: hidden;
}
.preview-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.preview-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transition: opacity .3s;
}
.preview-card:hover .preview-overlay {
  opacity: 1;
}
</style>
