/**
 * 系统管理 API — 全部对接真实后端
 */
import request from './request'

// ==================== 用户管理 — /api/v1/admin/users ====================
export const fetchUsers = (params) => request.get('/admin/users', { params })
export const createUser = (data) => request.post('/admin/users', data)
export const updateUser = (id, data) => request.patch(`/admin/users/${id}`, data)

// ==================== 角色管理 — /api/v1/admin/roles ====================
export const getRoles = () => request.get('/admin/roles')
export const createRole = (data) => request.post('/admin/roles', data)
export const updateRole = (id, data) => request.patch(`/admin/roles/${id}`, data)
export const deleteRole = (id) => request.delete(`/admin/roles/${id}`)

// ==================== 摄像头管理 — /api/v1/admin/cameras ====================
export const fetchCameras = (params) => request.get('/admin/cameras', { params })
export const createCamera = (data) => request.post('/admin/cameras', data)
export const updateCamera = (id, data) => request.patch(`/admin/cameras/${id}`, data)
export const generateKey = (deviceId) => request.post(`/admin/cameras/${deviceId}/keys`)
export const listKeys = (deviceId) => request.get(`/admin/cameras/${deviceId}/keys`)
export const revokeKey = (deviceId, keyId) => request.post(`/admin/cameras/${deviceId}/keys/${keyId}/revoke`)

// ==================== 审计日志 — /api/v1/admin/audit-logs ====================
export const fetchAuditLogs = (params) => request.get('/admin/audit-logs', { params })

// ==================== 奖励记录 — /api/v1/admin/rewards ====================
export const fetchRewards = (params) => request.get('/admin/rewards', { params })
