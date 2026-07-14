<template>
  <div class="case-detail" v-loading="loading">
    <!-- 顶部导航 -->
    <div class="top-bar">
      <el-button @click="router.back()" text><el-icon><ArrowLeft /></el-icon>返回列表</el-button>
      <div class="case-title">
        <span class="case-no">{{ detail.case_no }}</span>
        <el-tag :type="statusType(detail.status)">{{ statusText(detail.status) }}</el-tag>
      </div>
      <div class="case-meta">
        <span>{{ sourceIcon(detail.source_type) }} {{ detail.source_desc }}</span>
        <span>{{ formatTime(detail.captured_at) }}</span>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 左列：图片对比 -->
      <el-col :span="10">
        <!-- 原图 vs 标注图 -->
        <el-card class="image-card">
          <template #header>
            <el-tabs v-model="imageTab" size="small">
              <el-tab-pane label="原图" name="original" />
              <el-tab-pane label="AI 标注图" name="annotated" :disabled="!detail.media?.annotated_url" />
            </el-tabs>
          </template>
          <el-image
            :src="imageTab === 'original' ? detail.media?.original_url : detail.media?.annotated_url"
            fit="contain"
            style="width:100%;max-height:500px;min-height:300px"
            :preview-src-list="[detail.media?.original_url, detail.media?.annotated_url].filter(Boolean)"
          >
            <template #error><div class="img-empty"><el-icon :size="48"><Picture /></el-icon><p>暂无图片</p></div></template>
          </el-image>
        </el-card>

        <!-- 案件基本信息 -->
        <el-card style="margin-top:12px">
          <template #header><span>案件信息</span></template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="来源">{{ sourceTypeMap[detail.source_type] || detail.source_type }}</el-descriptions-item>
            <el-descriptions-item label="地点">{{ detail.location_text }}</el-descriptions-item>
            <el-descriptions-item label="时间">{{ formatTime(detail.captured_at) }}</el-descriptions-item>
            <el-descriptions-item label="车速" v-if="detail.speed">{{ detail.speed }} km/h</el-descriptions-item>
            <el-descriptions-item label="举报违法类型" v-if="detail.reported_violation_type">
              {{ detail.reported_violation_type }}
            </el-descriptions-item>
            <el-descriptions-item label="车牌">
              {{ detail.plate_no || detail.plate_status_message || '待识别' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- 右列：AI 全链路 + 审核操作 -->
      <el-col :span="14">
        <!-- AI 全链路 Panel -->
        <el-card class="pipeline-card">
          <template #header>
            <span style="font-weight:600">🔍 AI 识别全链路</span>
          </template>

          <el-collapse v-model="activeSteps" accordion>
            <!-- 第1步：YOLOv8 目标检测 -->
            <el-collapse-item name="detection">
              <template #title>
                <div class="step-title">
                  <span class="step-num">①</span>
                  <span>YOLOv8 目标检测</span>
                  <el-tag v-if="detail.detection_result" size="small" type="success">已完成</el-tag>
                  <el-tag v-else size="small" type="info">等待中</el-tag>
                </div>
              </template>
              <template v-if="detail.detection_result">
                <el-descriptions :column="1" border size="small">
                  <el-descriptions-item label="模型版本">{{ detail.detection_result.model_version }}</el-descriptions-item>
                </el-descriptions>
                <div class="detected-items">
                  <el-tag
                    v-for="(obj, index) in (detail.detection_result.objects || detail.detection_result.detected_objects)"
                    :key="obj.detection_id || `${obj.label}-${index}`"
                    size="small"
                    :type="obj.is_primary ? 'danger' : obj.confidence > 0.9 ? 'success' : obj.confidence > 0.8 ? 'warning' : 'info'"
                    style="margin:4px 4px 0 0"
                  >
                    {{ obj.display_label || objLabel(obj.label) }} {{ (obj.confidence * 100).toFixed(0) }}%
                    <strong v-if="obj.is_primary"> · 主目标</strong>
                  </el-tag>
                </div>
              </template>
              <el-empty v-else description="暂无检测结果" :image-size="40" />
            </el-collapse-item>

            <!-- 第2步：OCR 车牌识别 -->
            <el-collapse-item name="ocr">
              <template #title>
                <div class="step-title">
                  <span class="step-num">②</span>
                  <span>OCR 车牌识别</span>
                  <el-tag v-if="detail.plate_no" size="small" type="success">已识别</el-tag>
                  <el-tag v-else-if="detail.plate_status" size="small" type="warning">未识别</el-tag>
                  <el-tag v-else size="small" type="info">等待中</el-tag>
                </div>
              </template>
              <template v-if="detail.plate_no">
                <el-result icon="success" :title="detail.plate_no" sub-title="车牌识别成功" size="small" />
              </template>
              <el-alert
                v-else-if="detail.plate_status_message"
                :title="detail.plate_status_message"
                :type="detail.plate_status === 'skipped_no_violation' ? 'info' : 'warning'"
                :closable="false"
                show-icon
              />
              <el-empty v-else description="等待车牌识别" :image-size="40" />
            </el-collapse-item>

            <!-- 第3步：规则判定 -->
            <el-collapse-item name="rule">
              <template #title>
                <div class="step-title">
                  <span class="step-num">③</span>
                  <span>规则判定</span>
                  <el-tag v-if="detail.rule_result?.rule_matched" size="small" :type="detail.rule_result.evidence_level === 'complete' ? 'success' : 'warning'">已匹配</el-tag>
                  <el-tag v-else-if="detail.rule_result" size="small" type="info">不匹配</el-tag>
                  <el-tag v-else size="small" type="info">等待中</el-tag>
                </div>
              </template>
              <template v-if="detail.rule_result">
                <el-descriptions :column="1" border size="small">
                  <el-descriptions-item label="违章候选">{{ detail.rule_result.candidate_violation_type }}</el-descriptions-item>
                  <el-descriptions-item label="主违法目标" v-if="detail.detection_result?.primary_target">
                    {{ detail.detection_result.primary_target.vehicle.display_label || detail.detection_result.primary_target.vehicle.detection_id }}
                  </el-descriptions-item>
                  <el-descriptions-item label="规则编号">{{ detail.rule_result.rule_code }}</el-descriptions-item>
                  <el-descriptions-item label="证据完整度">
                    <el-tag :type="detail.rule_result.evidence_level === 'complete' ? 'success' : 'warning'" size="small">
                      {{ evidenceLevelText(detail.rule_result.evidence_level) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="已有证据">{{ detail.rule_result.evidence_items?.join('、') }}</el-descriptions-item>
                  <el-descriptions-item label="缺失证据" v-if="detail.rule_result.missing_evidence?.length">
                    <span style="color:#f56c6c">{{ detail.rule_result.missing_evidence?.join('、') }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="判定说明">{{ detail.rule_result.reason }}</el-descriptions-item>
                </el-descriptions>
              </template>
              <el-empty v-else description="暂无规则判定结果" :image-size="40" />
            </el-collapse-item>

            <!-- 第4步：AI 初审 / 多模态复核 -->
            <el-collapse-item name="review">
              <template #title>
                <div class="step-title">
                  <span class="step-num">④</span>
                  <span>{{ detail.ai_review?.review_mode === 'vision_llm' ? '多模态复核' : 'AI 初审' }}</span>
                  <el-tag v-if="detail.ai_review" size="small" :type="aiTag(detail.ai_review.conclusion)">
                    {{ aiText(detail.ai_review.conclusion) }}
                  </el-tag>
                  <el-tag v-else size="small" type="info">等待中</el-tag>
                </div>
              </template>
              <template v-if="detail.ai_review">
                <el-descriptions :column="1" border size="small">
                  <el-descriptions-item label="审查模式">
                    {{ detail.ai_review.review_mode === 'vision_llm' ? '多模态模型复核' : '文本 LLM 初审' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="结论">
                    <el-tag :type="aiTag(detail.ai_review.conclusion)">{{ aiText(detail.ai_review.conclusion) }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="AI 置信度">{{ (detail.ai_review.ai_confidence * 100).toFixed(0) }}%</el-descriptions-item>
                  <el-descriptions-item label="初审理由">{{ detail.ai_review.reason }}</el-descriptions-item>
                  <el-descriptions-item label="风险点" v-if="detail.ai_review.risk_points?.length">
                    <span style="color:#e6a23c">{{ detail.ai_review.risk_points?.join('；') }}</span>
                  </el-descriptions-item>
                </el-descriptions>
              </template>
              <el-empty v-else description="等待 AI 初审" :image-size="40" />
            </el-collapse-item>
          </el-collapse>
        </el-card>

        <!-- 审核操作面板 -->
        <el-card class="review-panel" v-if="['uploaded','detecting','ai_reviewing','pending_human_review'].includes(detail.status)">
          <template #header><span style="font-weight:600">✍️ 人工审核</span></template>
          <el-form :model="reviewForm" label-width="100px">
            <el-form-item label="车牌号">
              <el-input v-model="reviewForm.plate_no" placeholder="确认或补录车牌号" />
            </el-form-item>
            <el-form-item label="违章类型">
              <el-select v-model="reviewForm.violation_type" placeholder="选择违章类型" style="width:100%">
                <el-option v-for="t in violationTypes" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
            <el-form-item label="罚款金额" v-if="reviewForm.action === 'approve'">
              <el-input-number v-model="reviewForm.fine_amount" :min="0" :max="5000" :step="50" style="width:100%" />
            </el-form-item>
            <el-form-item label="扣分" v-if="reviewForm.action === 'approve'">
              <el-input-number v-model="reviewForm.points" :min="0" :max="12" :step="1" style="width:100%" />
            </el-form-item>
            <el-form-item label="审核意见">
              <el-input v-model="reviewForm.review_opinion" type="textarea" :rows="3" placeholder="填写审核意见" />
            </el-form-item>
            <el-form-item>
              <el-button type="success" :loading="submitting" @click="handleApprove">审核通过</el-button>
              <el-button type="danger" :loading="submitting" @click="handleReject">驳回</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 已审核结果展示 -->
        <el-card v-else-if="isApprovedCaseStatus(detail.status) || detail.status === 'rejected'" style="margin-top:12px">
          <template #header><span>审核结果</span></template>
          <el-result
            :icon="isApprovedCaseStatus(detail.status) ? 'success' : 'error'"
            :title="isApprovedCaseStatus(detail.status) ? '已审核通过' : '已驳回'"
            :sub-title="getCaseReviewOpinion(detail)"
          >
            <template #extra v-if="detail.violation_type">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="违章类型">{{ detail.violation_type }}</el-descriptions-item>
                <el-descriptions-item label="车牌号">{{ detail.plate_no }}</el-descriptions-item>
              </el-descriptions>
            </template>
          </el-result>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchCaseDetail as getCaseDetail, approveCase, rejectCase } from '@/api/case'
import { fetchProtectedMediaUrl } from '@/api/media'
import {
  buildApprovePayload,
  buildRejectPayload,
  createLatestRequestGuard,
  getCaseReviewOpinion,
  isApprovedCaseStatus,
  loadProtectedMediaUrls,
  releaseProtectedMediaUrls
} from '@/utils/contracts'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const detail = ref({})
const loading = ref(false)
const submitting = ref(false)
const imageTab = ref('original')
const activeSteps = ref('detection')
const mediaRequestGuard = createLatestRequestGuard()

const violationTypes = ['疑似闯红灯', '闯红灯', '违停', '压线', '逆行', '超速', '占用应急车道', '不礼让行人', '不按导向行驶']

const reviewForm = reactive({
  action: 'approve',
  plate_no: '',
  violation_type: '',
  fine_amount: 200,
  points: 3,
  review_opinion: ''
})

const sourceTypeMap = { citizen: '市民举报', camera: '摄像头抓拍', admin: '后台上传' }
const statusMap = {
  uploaded: '待审核', detecting: '识别中', ai_reviewing: 'AI 初审中',
  pending_human_review: '待审核', approved: '已通过', rejected: '已驳回',
  archived: '已归档', notified: '已通知'
}
const evidenceMap = { complete: '证据完整', partial: '部分完整', insufficient: '证据不足', 完整: '证据完整', 部分: '部分完整', 不足: '证据不足' }
const aiMap = { suggest_approve: '建议通过', need_review: '建议复核', suggest_reject: '建议驳回', 建议通过: '建议通过', 需人工审核: '建议复核', 建议驳回: '建议驳回' }
const aiTypeMap = { suggest_approve: 'success', need_review: 'warning', suggest_reject: 'danger', 建议通过: 'success', 需人工审核: 'warning', 建议驳回: 'danger' }
const objLabelMap = { cars: '小汽车', car: '小汽车', bus: '公交车', truck: '卡车', van: '面包车', illegal: '违停', 'chinese-plate-license': '车牌', vehicle: '车辆', plate: '车牌' }

function statusText(s) { return statusMap[s] || s }
function statusType(s) {
  const m = {
    uploaded: 'danger', pending_human_review: 'danger', approved: 'success',
    rejected: 'info', detecting: 'warning', ai_reviewing: 'warning', notified: 'success'
  }
  return m[s] || 'info'
}
function sourceIcon(s) { return s === 'citizen' ? '📱' : s === 'camera' ? '📷' : '👤' }
function formatTime(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }
function evidenceLevelText(e) { return evidenceMap[e] || e }
function aiText(c) { return aiMap[c] || c }
function aiTag(c) { return aiTypeMap[c] || 'info' }
function objLabel(l) { return objLabelMap[l] || l }

async function fetchDetail() {
  const requestGeneration = mediaRequestGuard.begin()
  loading.value = true
  try {
    const res = await getCaseDetail(route.params.id)
    const nextDetail = {
      ...res.data,
      media: await loadProtectedMediaUrls(res.data.media, fetchProtectedMediaUrl)
    }
    if (!mediaRequestGuard.isCurrent(requestGeneration)) {
      releaseProtectedMediaUrls(nextDetail.media)
      return
    }
    releaseProtectedMediaUrls(detail.value.media)
    detail.value = nextDetail
    // 填充审核表单默认值
    reviewForm.plate_no = detail.value.plate_no || ''
    reviewForm.violation_type = detail.value.rule_result?.candidate_violation_type || detail.value.reported_violation_type || ''
  } catch {
    if (mediaRequestGuard.isCurrent(requestGeneration)) ElMessage.error('加载案件失败')
  } finally {
    if (mediaRequestGuard.isCurrent(requestGeneration)) loading.value = false
  }
}

async function handleApprove() {
  submitting.value = true
  try {
    await approveCase(route.params.id, buildApprovePayload(reviewForm))
    ElMessage.success('审核通过，违章记录已生成')
    router.push('/review/workbench')
  } catch { ElMessage.error('操作失败') }
  finally { submitting.value = false }
}

async function handleReject() {
  if (!reviewForm.review_opinion) {
    ElMessage.warning('请填写驳回原因')
    return
  }
  submitting.value = true
  try {
    await rejectCase(route.params.id, buildRejectPayload(reviewForm))
    ElMessage.success('案件已驳回')
    router.push('/review/workbench')
  } catch { ElMessage.error('操作失败') }
  finally { submitting.value = false }
}

onMounted(fetchDetail)
onUnmounted(() => {
  mediaRequestGuard.invalidate()
  releaseProtectedMediaUrls(detail.value.media)
})
</script>

<style scoped>
.case-detail { display: flex; flex-direction: column; gap: 16px; }
.top-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}
.case-title { display: flex; align-items: center; gap: 8px; }
.case-no { font-weight: 600; font-size: 16px; }
.case-meta { margin-left: auto; display: flex; gap: 16px; font-size: 13px; color: var(--text-secondary); }

.image-card { }
.img-empty {
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.pipeline-card { }
.step-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}
.step-num { color: #72a8c4; font-weight: bold; }
.detected-items { padding: 8px 0; }

.review-panel { margin-top: 12px; }
</style>
