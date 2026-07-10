/**
 * 案件管理 API — 连接真实后端
 */
import request from './request'

export const getCases = async (params = {}) => {
  const res = await request.get('/cases', { params })
  // 后端返回 {items, total, page, page_size}，映射为前端的 {list, total, page, page_size}
  return { ...res, data: { list: res.data.items, total: res.data.total, page: res.data.page, page_size: res.data.page_size } }
}

export const getCaseDetail = (id) => request.get(`/cases/${id}`)

export const approveCase = (id, data) => request.post(`/cases/${id}/approve`, data)

export const rejectCase = (id, data) => request.post(`/cases/${id}/reject`, data)

export const requestRecheck = (id) => request.post(`/cases/${id}/request-recheck`)
