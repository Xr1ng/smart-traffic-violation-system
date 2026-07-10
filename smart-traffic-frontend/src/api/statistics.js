/**
 * 统计分析 API — 对齐 API接口规范文档 v2.0 §6
 */
import { ok, delay, mockStatistics } from './mock'
import request from './request'

// ==================== Mock API (保留兜底) ====================
export const getStatisticsOverview = async () => { await delay(); return ok(mockStatistics.overview) }
export const getStatisticsByLocation = async () => { await delay(); return ok(mockStatistics.regionRank) }
export const getStatisticsByTime = async () => { await delay(); return ok(mockStatistics.trend) }
export const getStatisticsByType = async () => { await delay(); return ok(mockStatistics.typeRatio) }

export const getOverview = async () => { await delay(); return ok(mockStatistics.overview) }
export const getTrend = async () => { await delay(); return ok(mockStatistics.trend) }
export const getTypeRatio = async () => { await delay(); return ok(mockStatistics.typeRatio) }
export const getRegionRank = async () => { await delay(); return ok(mockStatistics.regionRank) }

// ==================== 真实后端（张浩-5，reviewer/admin 鉴权）====================
export const fetchOverview = (params) => request.get('/statistics/overview', { params })
export const fetchByLocation = (params) => request.get('/statistics/by-location', { params })
export const fetchByType = (params) => request.get('/statistics/by-type', { params })
export const fetchByTime = (params) => request.get('/statistics/by-time', { params })
export const generateReport = (data) => request.post('/analysis/reports', data)
