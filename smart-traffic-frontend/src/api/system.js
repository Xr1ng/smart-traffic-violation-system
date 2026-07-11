/**
 * 系统管理 API — 对齐 API接口规范文档 v2.0 §7
 */
import { ok, pageOk, delay, mockUsers, mockCameras } from './mock'
import request from './request'

const mockRoles = [
  { id: 1, name: '超级管理员', key: 'admin', description: '系统最高权限', permissions: ['all'] },
  { id: 2, name: '审核员', key: 'reviewer', description: '审核违章案件', permissions: ['review', 'view'] },
  { id: 3, name: '市民', key: 'citizen', description: '普通市民用户', permissions: ['report', 'view_my'] }
]

const mockRules = [
  { id: 1, type_code: 'red_light', name: '闯红灯', description: '车辆越过停止线时红灯亮起', fine_amount: 200, points: 6, enabled: true },
  { id: 2, type_code: 'parking', name: '违停', description: '在禁止停车区域停放', fine_amount: 200, points: 3, enabled: true },
  { id: 3, type_code: 'lane_cross', name: '压线', description: '车辆跨越实线变道', fine_amount: 200, points: 3, enabled: true },
  { id: 4, type_code: 'reverse', name: '逆行', description: '在道路上逆向行驶', fine_amount: 200, points: 3, enabled: true },
  { id: 5, type_code: 'speed', name: '超速', description: '超过限速行驶', fine_amount: 500, points: 6, enabled: true },
  { id: 6, type_code: 'emergency_lane', name: '占用应急车道', description: '非紧急情况占用应急车道', fine_amount: 200, points: 6, enabled: true }
]

const mockTemplates = [
  { id: 1, name: '违章通知', code: 'violation_notify', content: '【交通违章通知】您的车辆{plate_no}于{date}在{location}发生{violation_type}，罚款{amount}元，记{points}分，请及时处理。', enabled: true },
  { id: 2, name: '举报奖励', code: 'report_reward', content: '【举报奖励通知】您的举报（单号{RPT000001}）已核实，奖励{amount}元已发放至您的账户。', enabled: true },
  { id: 3, name: '案件驳回', code: 'case_rejected', content: '【案件驳回通知】您的举报（单号{RPT000001}）因{reason}被驳回，感谢您的参与。', enabled: true }
]

const mockLogs = Array.from({ length: 20 }, (_, i) => ({
  id: i + 1,
  user_id: mockUsers[i % mockUsers.length].id,
  username: mockUsers[i % mockUsers.length].username,
  action: ['登录系统', '审核案件', '查询违章', '导出数据', '修改配置'][i % 5],
  target_type: ['case', 'violation', 'system', 'user', 'config'][i % 5],
  target_id: i + 100,
  ip: `192.168.1.${Math.floor(Math.random() * 255)}`,
  created_at: new Date(Date.now() - i * 3600000).toISOString()
}))

// 用户管理
export const getUsers = async (params = {}) => {
  await delay()
  const { page = 1, page_size = 10, keyword, role } = params
  let filtered = [...mockUsers]
  if (keyword) filtered = filtered.filter(u => u.username.includes(keyword))
  if (role) filtered = filtered.filter(u => u.role === role)
  return pageOk(filtered, filtered.length, page, page_size)
}

export const updateUserRole = async (id, data) => {
  await delay(300)
  return ok({ id, role: data.role, message: '角色已更新' })
}

export const toggleUserStatus = async (id, data) => {
  await delay(300)
  return ok({ id, status: data.status, message: '状态已更新' })
}

// 角色管理 — 真实 API
export const getRoles = () => request.get('/admin/roles')

export const createRole = async (data) => {
  await delay(300)
  return ok({ id: 99, ...data, message: '角色创建成功' })
}

export const updateRole = async (id, data) => {
  await delay(300)
  return ok({ id, ...data, message: '角色更新成功' })
}

export const deleteRole = async (id) => {
  await delay(300)
  return ok({ id, message: '角色删除成功' })
}

export const updateRolePermissions = async (id, data) => {
  await delay(300)
  return ok({ id, permissions: data.permissions, message: '权限已更新' })
}

// 摄像头管理
export const getCameras = async (params = {}) => {
  await delay()
  return pageOk(mockCameras, mockCameras.length)
}

export const deleteCamera = async (id) => {
  await delay(300)
  return ok({ id, message: '摄像头删除成功' })
}

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

// 通知模块
export const getNotifications = async (params = {}) => {
  await delay()
  return pageOk([], 0)
}

export const getNotificationsByViolation = async (violationId) => {
  await delay()
  return ok([])
}

// ==================== 真实后端（张浩-7/8，admin 鉴权）====================
// 用户管理 — /api/v1/admin/users
export const fetchUsers = (params) => request.get('/admin/users', { params })
export const createUser = (data) => request.post('/admin/users', data)
export const updateUser = (id, data) => request.patch(`/admin/users/${id}`, data)

// 摄像头管理 — /api/v1/admin/cameras
export const fetchCameras = (params) => request.get('/admin/cameras', { params })
export const createCamera = (data) => request.post('/admin/cameras', data)
export const updateCamera = (id, data) => request.patch(`/admin/cameras/${id}`, data)
export const generateKey = (deviceId) => request.post(`/admin/cameras/${deviceId}/keys`)
export const listKeys = (deviceId) => request.get(`/admin/cameras/${deviceId}/keys`)
export const revokeKey = (deviceId, keyId) => request.post(`/admin/cameras/${deviceId}/keys/${keyId}/revoke`)

// 违章规则 — /api/v1/admin/rules
export const fetchRules = (params) => request.get('/admin/rules', { params })
export const createRule = (data) => request.post('/admin/rules', data)
export const updateRule = (id, data) => request.patch(`/admin/rules/${id}`, data)

// 审计日志 — /api/v1/admin/audit-logs
export const fetchAuditLogs = (params) => request.get('/admin/audit-logs', { params })

// 奖励记录 — /api/v1/admin/rewards
export const fetchRewards = (params) => request.get('/admin/rewards', { params })
