/**
 * 系统管理 API — 连接真实后端
 */
import request from './request'

// ===================== 用户管理 =====================
export const getUsers = (params) => request.get('/admin/users', { params })
export const getUser = (id) => request.get(`/admin/users/${id}`)
export const createUser = (data) => request.post('/admin/users', data)
export const updateUser = (id, data) => request.patch(`/admin/users/${id}`, data)

// 兼容旧版接口名
export const updateUserRole = (id, data) => request.patch(`/admin/users/${id}`, data)
export const toggleUserStatus = (id, data) => request.patch(`/admin/users/${id}`, data)

// ===================== 摄像头管理 =====================
export const getCameras = (params) => request.get('/admin/cameras', { params })
export const getCamera = (id) => request.get(`/admin/cameras/${id}`)
export const createCamera = (data) => request.post('/admin/cameras', data)
export const updateCamera = (id, data) => request.patch(`/admin/cameras/${id}`, data)

// API Key 管理
export const getApiKeys = async (cameraId) => {
  await delay()
  return ok([{ id: 1, key: 'sk-cam-001', created_at: new Date().toISOString() }])
}

export const createApiKey = async (cameraId, data) => {
  await delay(300)
  return ok({ key: 'sk-cam-new', message: 'API Key 创建成功' })
}

export const revokeApiKey = async (id) => {
  await delay(300)
  return ok({ id, message: 'API Key 已撤销' })
}

// 违章规则配置
export const getViolationRules = async () => {
  await delay()
  return ok(mockRules)
}

export const updateViolationRule = async (id, data) => {
  await delay(300)
  return ok({ id, ...data, message: '规则更新成功' })
}

// 短信模板
export const getSmsTemplates = async () => {
  await delay()
  return ok(mockTemplates)
}

export const updateSmsTemplate = async (id, data) => {
  await delay(300)
  return ok({ id, ...data, message: '模板更新成功' })
}

// 操作日志
export const getAuditLogs = async (params = {}) => {
  await delay()
  return pageOk(mockLogs, mockLogs.length)
}

// 公告管理
const mockAnnouncements = [
  { id: 1, title: '系统升级通知', content: '系统将于本周六凌晨2:00-4:00进行升级维护，届时暂停服务。', created_at: '2026-07-05 10:00:00' },
  { id: 2, title: '新版违章举报功能上线', content: '新版随手拍功能已上线，支持多张图片上传，AI识别更精准。', created_at: '2026-07-03 09:00:00' }
]

export const getAnnouncements = async () => {
  await delay()
  return ok(mockAnnouncements)
}

export const createAnnouncement = async (data) => {
  await delay(300)
  return ok({ id: Date.now(), ...data, message: '公告发布成功' })
}

export const updateAnnouncement = async (id, data) => {
  await delay(300)
  return ok({ id, ...data, message: '公告更新成功' })
}

export const deleteAnnouncement = async (id) => {
  await delay(300)
  return ok({ id, message: '公告删除成功' })
}

// 数据库维护
export const backupDatabase = async () => {
  await delay(1000)
  return ok({ filename: `backup_${Date.now()}.sql`, size: '12.5MB', message: '数据库备份成功' })
}

// 系统日志（复用审计日志 mock 数据）
export const getLogs = getAuditLogs

// 通知模块
export const getNotifications = async (params = {}) => {
  await delay()
  return pageOk([], 0)
}

export const getNotificationsByViolation = async (violationId) => {
  await delay()
  return ok([])
}
