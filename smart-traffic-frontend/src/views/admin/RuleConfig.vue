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

const STORAGE_KEY = 'app_violation_rules'

// 内置默认规则数据
const DEFAULT_RULES = [
  { id: 1, rule_code: 'RED_LIGHT', violation_type: '闯红灯', rule_type: '交通信号', params: '{"points":6,"fine":500}', description: '机动车违反交通信号灯指示行驶，记6分，罚款500元', is_active: true },
  { id: 2, rule_code: 'SPEEDING_20', violation_type: '超速20%以下', rule_type: '超速', params: '{"points":3,"fine":200}', description: '超过限速不足20%的，记3分，罚款200元', is_active: true },
  { id: 3, rule_code: 'SPEEDING_20_50', violation_type: '超速20%-50%', rule_type: '超速', params: '{"points":6,"fine":500}', description: '超过限速20%以上不足50%的，记6分，罚款500元', is_active: true },
  { id: 4, rule_code: 'SPEEDING_50', violation_type: '超速50%以上', rule_type: '超速', params: '{"points":12,"fine":2000}', description: '超过限速50%以上的，记12分，罚款2000元', is_active: true },
  { id: 5, rule_code: 'WRONG_WAY', violation_type: '逆向行驶', rule_type: '行驶方向', params: '{"points":3,"fine":200}', description: '机动车逆向行驶，记3分，罚款200元', is_active: true },
  { id: 6, rule_code: 'NO_ENTRY', violation_type: '违反禁行标志', rule_type: '交通信号', params: '{"points":3,"fine":200}', description: '违反禁止通行标志指示行驶，记3分，罚款200元', is_active: true },
  { id: 7, rule_code: 'ILLEGAL_PARKING', violation_type: '违章停车', rule_type: '停放', params: '{"points":0,"fine":200}', description: '在禁止停车路段停放车辆，罚款200元', is_active: true },
  { id: 8, rule_code: 'NO_SEATBELT', violation_type: '未系安全带', rule_type: '安全驾驶', params: '{"points":1,"fine":50}', description: '驾驶机动车未按规定使用安全带，记1分，罚款50元', is_active: true },
  { id: 9, rule_code: 'PHONE_USE', violation_type: '驾车使用手机', rule_type: '安全驾驶', params: '{"points":3,"fine":200}', description: '驾驶过程中使用手持电话，记3分，罚款200元', is_active: true },
  { id: 10, rule_code: 'DRUNK_DRIVING', violation_type: '酒驾', rule_type: '严重违章', params: '{"points":12,"fine":2000}', description: '饮酒后驾驶机动车，记12分，罚款2000元，暂扣驾照6个月', is_active: true },
  { id: 11, rule_code: 'OVERLOAD', violation_type: '超载', rule_type: '载重', params: '{"points":6,"fine":500}', description: '载客或载货超过核定载重，记6分，罚款500元', is_active: true },
  { id: 12, rule_code: 'LINE_CHANGE', violation_type: '违法变道', rule_type: '行驶规范', params: '{"points":3,"fine":200}', description: '压实线变道或不按规定变更车道，记3分，罚款200元', is_active: true }
]

function loadLocalRules() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

function saveLocalRules(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

function ensureDefaults() {
  const local = loadLocalRules()
  if (local.length === 0) {
    saveLocalRules(DEFAULT_RULES)
    return [...DEFAULT_RULES]
  }
  return local
}

function getNextLocalId() {
  const local = loadLocalRules()
  if (local.length === 0) return 13
  return Math.max(...local.map(r => r.id), 0) + 1
}

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
    if (res.data.items && res.data.items.length > 0) {
      rules.value = res.data.items
    } else {
      // 后端返回空，使用本地数据
      rules.value = ensureDefaults()
    }
    return true
  } catch {
    // 后端不可用时，使用本地数据兜底
    rules.value = ensureDefaults()
    return true
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

    // 尝试调用后端 API
    let serverOk = false
    try {
      if (dialog.isEdit) await updateRule(dialog.id, payload)
      else await createRule({ rule_code: form.rule_code, ...payload })
      serverOk = true
    } catch {}

    // 同时更新本地缓存
    const local = loadLocalRules()
    if (dialog.isEdit) {
      const idx = local.findIndex(r => r.id === dialog.id)
      if (idx !== -1) {
        local[idx] = { ...local[idx], ...payload, rule_code: form.rule_code }
        saveLocalRules(local)
      }
    } else {
      local.push({
        id: getNextLocalId(),
        rule_code: form.rule_code,
        ...payload,
        is_active: true
      })
      saveLocalRules(local)
    }

    dialog.visible = false
    if (serverOk) await loadRules()
    else rules.value = loadLocalRules()
    ElMessage.success('保存成功' + (serverOk ? '' : '（已保存至本地）'))
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
  } catch {
    // 后端失败也更新本地
  }
  // 同步本地数据
  const local = loadLocalRules()
  const idx = local.findIndex(r => r.id === row.id)
  if (idx !== -1) {
    local[idx].is_active = row.is_active
    saveLocalRules(local)
  }
  const next = new Set(togglingIds.value)
  next.delete(row.id)
  togglingIds.value = next
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
