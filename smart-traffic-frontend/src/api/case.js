/**
 * 案件管理 API — 对齐 API接口规范文档 v2.0 §4
 */
import request from './request'

// 真实后端（杨翼 M3，reviewer/admin 鉴权）
export const fetchCases = (p) => request.get('/cases', { params: p })
export const fetchCaseDetail = (id) => request.get('/cases/' + id)
export const approveCase = (id, d) => request.post('/cases/' + id + '/approve', d)
export const rejectCase = (id, d) => request.post('/cases/' + id + '/reject', d)
export const requestRecheck = (id) => request.post('/cases/' + id + '/request-recheck')
