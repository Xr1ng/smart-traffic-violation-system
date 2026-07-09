/**
 * 违章管理 API — 对齐 API接口规范文档 v2.0 §5
 */
import { ok, pageOk, err, delay, mockViolations, mockReports } from './mock'

// ==================== Mock API (默认使用) ====================
export const getViolations = async (params = {}) => {
  await delay()
  const { page = 1, page_size = 10, plate_no, violation_type, status } = params
  let filtered = [...mockViolations]

  if (plate_no) filtered = filtered.filter(v => v.plate_no.includes(plate_no))
  if (violation_type) filtered = filtered.filter(v => v.violation_type === violation_type)
  if (status) filtered = filtered.filter(v => v.status === status)

  const total = filtered.length
  const start = (page - 1) * page_size
  const list = filtered.slice(start, start + page_size)

  return pageOk(list, total, page, page_size)
}

export const getViolationDetail = async (id) => {
  await delay()
  const v = mockViolations.find(v => v.id === Number(id))
  return v ? ok(v) : err('违章记录不存在', 404)
}

export const manualNotify = async (id) => {
  await delay(400)
  return ok({ violation_id: id, status: 'sent', message: '短信通知已发送' })
}

export const getOwnerViolations = async (ownerId, params = {}) => {
  await delay()
  const { page = 1, page_size = 10 } = params
  const filtered = mockViolations.filter(v => v.owner_id === Number(ownerId))
  return pageOk(filtered, filtered.length, page, page_size)
}

export const exportExcel = async (params) => {
  await delay()
  return ok({ message: '导出成功' })
}

export const submitReport = async (data) => {
  await delay(500)
  return ok({
    id: Date.now(),
    status: 'uploaded',
    message: '举报提交成功，等待审核'
  })
}

export const getReports = async (params = {}) => {
  await delay()
  const { page = 1, page_size = 10, status } = params
  let filtered = [...mockReports]
  if (status) filtered = filtered.filter(r => r.status === status)
  return pageOk(filtered, filtered.length, page, page_size)
}

// ViolationReview.vue 中所用函数
export const getViolation = getViolationDetail

export const getAiResult = async (id) => {
  await delay()
  return ok({
    ai_result: '有效',
    ai_type: '闯红灯',
    ai_confidence: '96.3%',
    ai_plate: '京A·12345',
    ai_speed_limit: '60',
    ai_reason: '车辆在红灯亮起后越过停止线继续行驶，证据链完整。'
  })
}

export const reviewViolation = async (id, data) => {
  await delay(400)
  return ok({ id, action: data.action, message: data.action === 'approved' ? '审核通过，已生成违章记录' : '案件已驳回' })
}

// ViolationUpload.vue 中所用函数
export const createViolation = async (formData) => {
  await delay(500)
  return ok({ id: Date.now(), status: 'uploaded', message: '违章记录已创建，AI 识别任务已投递' })
}

export const uploadImage = async (formData) => {
  await delay(400)
  return ok({ url: '/mock/image/uploaded.jpg', message: '图片上传成功' })
}
