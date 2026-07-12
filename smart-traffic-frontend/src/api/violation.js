/**
 * 违章管理 API — 对齐 API接口规范文档 v2.0 §5
 */
import request from './request'

// 真实后端（杨翼 M3）
export const fetchViolations = (p) => request.get('/violations', { params: p })
export const fetchViolationDetail = (id) => request.get('/violations/' + id)
export const fetchOwnerViolations = (oid) => request.get('/owners/' + oid + '/violations')
