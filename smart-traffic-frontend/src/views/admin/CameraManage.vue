<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">摄像头设备管理</h2>
      <el-button type="primary" @click="openDialog()">新增设备</el-button>
    </div>

    <el-card>
      <el-table :data="cameras" border stripe>
        <el-table-column prop="camera_id" label="设备编号" width="120" />
        <el-table-column prop="name" label="设备名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="location_text" label="安装位置" width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '运行中' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="API Key" width="180">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="showKey(row)">查看/生成</el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="openDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCamera(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑设备' : '新增设备'" width="500px">
      <el-form :model="dialog.form" label-width="80px">
        <el-form-item label="设备编号">
          <el-input v-model="dialog.form.camera_id" :disabled="dialog.isEdit" placeholder="如：CAM-005" />
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input v-model="dialog.form.name" placeholder="如：人民路十字路口东" />
        </el-form-item>
        <el-form-item label="安装位置">
          <el-input v-model="dialog.form.location_text" placeholder="详细地址" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="dialog.form.status" active-value="active" inactive-value="inactive" active-text="运行" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" @click="saveCamera">保存</el-button>
      </template>
    </el-dialog>

    <!-- API Key 查看 -->
    <el-dialog v-model="keyDialog.visible" title="API Key" width="450px">
      <el-alert title="请妥善保管密钥，仅创建时展示一次" type="warning" :closable="false" show-icon style="margin-bottom:16px" />
      <el-input v-model="keyDialog.key" readonly>
        <template #append>
          <el-button @click="copyKey">复制</el-button>
        </template>
      </el-input>
      <template #footer>
        <el-button type="primary" @click="generateKey">生成新密钥</el-button>
        <el-button @click="keyDialog.visible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchCameras, createCamera, updateCamera, generateKey, revokeKey } from '@/api/system'
import { ElMessage, ElMessageBox } from 'element-plus'

const cameras = ref([])

const dialog = ref({
  visible: false,
  isEdit: false,
  form: { device_code: '', location_text: '', status: 'enabled' }
})

const keyDialog = ref({ visible: false, key: '', cameraId: null })

async function loadCameras() {
  const res = await fetchCameras({ page_size: 100 })
  cameras.value = res.data.items
}

function openDialog(row) {
  if (row) {
    dialog.value = { visible: true, isEdit: true, form: { ...row } }
  } else {
    dialog.value = { visible: true, isEdit: false, form: { device_code: '', location_text: '', status: 'enabled' } }
  }
}

async function saveCamera() {
  const f = dialog.value.form
  if (dialog.value.isEdit) {
    await updateCamera(f.id, { location_text: f.location_text, status: f.status })
  } else {
    await createCamera({ device_code: f.device_code, location_text: f.location_text })
  }
  dialog.value.visible = false; loadCameras(); ElMessage.success('保存成功')
}

function deleteCamera(row) {
  ElMessageBox.confirm('确定停用？', '确认', { type: 'warning' }).then(async () => {
    await updateCamera(row.id, { status: 'disabled' }); loadCameras()
    ElMessage.success('已停用')
  })
}

function showKey(row) { keyDialog.value = { visible: true, key: '', cameraId: row.id } }

async function doGenerateKey() {
  const res = await generateKey(keyDialog.value.cameraId)
  keyDialog.value.key = res.data.raw_key
  ElMessage.success('新密钥已生成（仅显示一次）')
}

function copyKey() { navigator.clipboard.writeText(keyDialog.value.key); ElMessage.success('已复制') }

onMounted(loadCameras)
</script>

<style scoped>
.page-container { }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { font-size: 20px; margin: 0; }
</style>
