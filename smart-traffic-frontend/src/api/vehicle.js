import request from './request'

// 车辆管理 — 后端 /api/v1/admin/vehicles（admin 鉴权，PATCH 更新）
export const getVehicles = (params) => request.get('/admin/vehicles', { params })
export const getVehicle = (id) => request.get(`/admin/vehicles/${id}`)
export const createVehicle = (data) => request.post('/admin/vehicles', data)
export const updateVehicle = (id, data) => request.patch(`/admin/vehicles/${id}`, data)
// 后端无硬删（Vehicle 模型无 status 字段）
export const deleteVehicle = (_id) => Promise.reject(new Error('暂不支持删除'))
// 后端无车主历史
export const getVehicleOwners = (_id) => Promise.reject(new Error('暂不支持'))

export const getMyVehicles = () => request.get('/vehicles/me')
export const bindMyVehicle = (data) => request.post('/vehicles/me', data)
export const unbindMyVehicle = (id) => request.delete(`/vehicles/me/${id}`)
