/**
 * 系统管理 API — 对齐 API接口规范文档 v2.0 §7
 */
import request from './request'

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
