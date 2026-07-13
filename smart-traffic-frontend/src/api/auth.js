import request from './request'

/**
 * 认证 API — 对齐 API接口规范文档 v2.0 §2
 */
export const login = (data) => request.post('/auth/login', data)
export const register = (data) => request.post('/auth/register', data)
export const getUserInfo = () => request.get('/auth/me')
export const updateProfile = (data) => request.put('/auth/profile', data)
export const changePassword = (data) => request.put('/auth/password', data)
export const getMenus = () => request.get('/permissions/menus')


