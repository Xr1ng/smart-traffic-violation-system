/**
 * 违章管理 API — 连接真实后端
 */
import request from './request'

export const getViolations = async (params = {}) => {
  const res = await request.get('/violations', { params })
  return { ...res, data: { list: res.data.items, total: res.data.total, page: res.data.page, page_size: res.data.page_size } }
}

export const getViolationDetail = (id) => request.get(`/violations/${id}`)

export const manualNotify = (id) => request.post(`/violations/${id}/notify`)

export const getOwnerViolations = async (ownerId, params = {}) => {
  const res = await request.get(`/owners/${ownerId}/violations`, { params })
  return { ...res, data: { list: res.data.items, total: res.data.total, page: res.data.page, page_size: res.data.page_size } }
}

export const exportExcel = (params) => request.get('/violations/export', { params, responseType: 'blob' })

// 市民举报 (转发到 intake)
export const submitReport = (formData) =>
  request.post('/intakes/citizen-reports', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

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
