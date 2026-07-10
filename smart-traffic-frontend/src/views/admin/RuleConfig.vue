<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">违章规则配置</h2>
      <el-button type="primary" @click="openCreateDialog">新增规则</el-button>
    </div>

    <el-card>
      <el-table :data="rules" border stripe v-loading="loading">
        <el-table-column prop="rule_code" label="规则编号" width="120" />
        <el-table-column prop="violation_type" label="违章类型" width="130" />
        <el-table-column prop="rule_type" label="规则类型" width="130" />
        <el-table-column prop="params" label="规则参数" min-width="180" show-overflow-tooltip />
        <el-table-column prop="description" label="规则描述" min-width="220" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              :loading="togglingIds.has(row.id)"
              :disabled="togglingIds.has(row.id)"
              @change="toggleRule(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button size="small" @click="editRule(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑规则' : '新增规则'" width="560px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="规则编号" prop="rule_code">
          <el-input v-model="form.rule_code" :disabled="dialog.isEdit" />
        </el-form-item>
        <el-form-item label="违章类型" prop="violation_type">
          <el-input v-model="form.violation_type" />
        </el-form-item>
        <el-form-item label="规则类型" prop="rule_type">
          <el-input v-model="form.rule_type" />
        </el-form-item>
        <el-form-item label="规则参数" prop="params">
          <el-input v-model="form.params" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="规则描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button :disabled="saving" @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createRule, fetchRules, updateRule } from '@/api/system'

const rules = ref([])
const loading = ref(false)
const saving = ref(false)
const togglingIds = ref(new Set())
const formRef = ref(null)
const dialog = reactive({ visible: false, isEdit: false, id: null })
const form = reactive({ rule_code: '', violation_type: '', rule_type: '', params: '', description: '' })
const formRules = {
  rule_code: [{ required: true, message: '请输入规则编号', trigger: 'blur' }],
  violation_type: [{ required: true, message: '请输入违章类型', trigger: 'blur' }],
  rule_type: [{ required: true, message: '请输入规则类型', trigger: 'blur' }]
}

function showUnexpectedError(error, message) {
  if (!error?.isAxiosError) ElMessage.error(message)
}

function resetForm() {
  Object.assign(form, { rule_code: '', violation_type: '', rule_type: '', params: '', description: '' })
  formRef.value?.clearValidate()
}

function openCreateDialog() {
  dialog.isEdit = false
  dialog.id = null
  resetForm()
  dialog.visible = true
}

function editRule(row) {
  dialog.isEdit = true
  dialog.id = row.id
  Object.assign(form, {
    rule_code: row.rule_code,
    violation_type: row.violation_type,
    rule_type: row.rule_type,
    params: row.params ?? '',
    description: row.description ?? ''
  })
  formRef.value?.clearValidate()
  dialog.visible = true
}

async function loadRules() {
  loading.value = true
  try {
    const res = await fetchRules({ page: 1, page_size: 100 })
    rules.value = res.data.items
    return true
  } catch (error) {
    showUnexpectedError(error, '规则加载失败')
    return false
  } finally {
    loading.value = false
  }
}

async function saveRule() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload = {
      violation_type: form.violation_type,
      rule_type: form.rule_type,
      params: form.params || null,
      description: form.description || null
    }
    if (dialog.isEdit) await updateRule(dialog.id, payload)
    else await createRule({ rule_code: form.rule_code, ...payload })
    dialog.visible = false
    if (await loadRules()) ElMessage.success('保存成功')
  } catch (error) {
    showUnexpectedError(error, '规则保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleRule(row) {
  togglingIds.value = new Set([...togglingIds.value, row.id])
  try {
    await updateRule(row.id, { is_active: row.is_active })
  } catch (error) {
    row.is_active = !row.is_active
    showUnexpectedError(error, '规则状态更新失败')
  } finally {
    const next = new Set(togglingIds.value)
    next.delete(row.id)
    togglingIds.value = next
  }
}

onMounted(loadRules)
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
