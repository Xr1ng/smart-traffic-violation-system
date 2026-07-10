/**
 * 统计分析 API — 连接真实后端
 */
import request from './request'

// 统计总览
export const getStatisticsOverview = (params) => request.get('/statistics/overview', { params })
// 按地点统计
export const getStatisticsByLocation = () => request.get('/statistics/by-location')
// 按时段统计
export const getStatisticsByTime = () => request.get('/statistics/by-time')
// 按类型统计
export const getStatisticsByType = () => request.get('/statistics/by-type')

// 兼容旧版函数名
export const getOverview = (params) => request.get('/statistics/overview', { params })
export const getTrend = () => request.get('/statistics/by-time')
export const getTypeRatio = () => request.get('/statistics/by-type')
export const getRegionRank = () => request.get('/statistics/by-location')
