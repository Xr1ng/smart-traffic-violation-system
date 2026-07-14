/**
 * 统计分析 API — 对齐 API接口规范文档 v2.0 §6
 */
import request from './request'

// ==================== 真实后端（张浩-5，reviewer/admin 鉴权）====================
export const fetchOverview = (params) => request.get('/statistics/overview', { params })
export const fetchByLocation = (params) => request.get('/statistics/by-location', { params })
export const fetchByType = (params) => request.get('/statistics/by-type', { params })
export const fetchByTime = (params) => request.get('/statistics/by-time', { params })
export const fetchRoadTimeHeatmap = (params) => request.get('/statistics/road-time-heatmap', { params })
export const generateReport = (data, options = {}) =>
  request.post('/analysis/reports', data, { timeout: 35000, ...options })
