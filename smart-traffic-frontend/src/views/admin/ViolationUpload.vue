<template>
  <div class="page-container" style="max-width:800px">
    <div class="page-header">
      <h2 class="page-title">证据图片上传</h2>
    </div>

    <el-card>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="上传来源">
          <el-radio-group v-model="form.source_type">
            <el-radio value="camera">摄像头抓拍</el-radio>
            <el-radio value="admin">后台上传</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="证据图片" prop="images">
          <el-upload
            :auto-upload="false"
            :on-change="handleChange"
            :before-remove="handleRemove"
            :file-list="fileList"
            list-type="picture-card"
            accept="image/*"
            :limit="3"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div style="color:#909399;font-size:12px;margin-top:4px">支持 jpg/png，最多上传 3 张</div>
        </el-form-item>

        <el-form-item label="拍摄地点" prop="location_text">
          <el-input v-model="form.location_text" placeholder="输入违章发生地点" />
        </el-form-item>

        <el-form-item label="拍摄时间" prop="captured_at">
          <el-date-picker v-model="form.captured_at" type="datetime" placeholder="选择时间" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" />
        </el-form-item>

        <el-form-item label="车速(km/h)" v-if="form.source_type === 'camera'">
          <el-input-number v-model="form.speed" :min="0" :max="300" style="width:100%" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">提交</el-button>
          <el-button @click="router.push('/admin/violations')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { adminUpload } from '@/api/intake'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)
const fileList = ref([])

const form = reactive({
  source_type: 'camera',
  location_text: '',
  captured_at: '',
  speed: null
})
const rules = {
  location_text: [{ required: true, message: '请输入地点', trigger: 'blur' }],
  captured_at: [{ required: true, message: '请选择时间', trigger: 'change' }]
}

function handleChange(file) { fileList.value.push(file) }
function handleRemove(file) {
  const i = fileList.value.indexOf(file)
  if (i > -1) fileList.value.splice(i, 1)
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (fileList.value.length === 0) { ElMessage.warning('请上传图片'); return }
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('location_text', form.location_text)
    fd.append('captured_at', form.captured_at)
    if (form.speed) fd.append('speed', form.speed)
    if (fileList.value.length > 0) {
      fd.append('image', fileList.value[0].raw)
    }
    await adminUpload(fd)
    ElMessage.success('上传成功，已投递 AI 识别任务')
    router.push('/admin/violations')
  } catch { /* handled */ }
  finally { submitting.value = false }
}
</script>

<style scoped>
.page-container { }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; margin: 0; }
</style>

