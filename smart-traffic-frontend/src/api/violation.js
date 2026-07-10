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
import request from './request'

// 真实后端（杨翼 M3）
export const fetchViolations = (p) => request.get('/violations', { params: p })
export const fetchViolationDetail = (id) => request.get('/violations/' + id)
export const fetchOwnerViolations = (oid) => request.get('/owners/' + oid + '/violations')
