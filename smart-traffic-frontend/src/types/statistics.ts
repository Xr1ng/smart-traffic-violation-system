/** 概览统计 */
export interface StatisticsOverview {
  total_cases: number
  total_violations: number
  approve_rate: number
  reject_rate: number
  pending_count: number
  today_new: number
}

/** 按类型统计项 */
export interface ViolationTypeItem {
  name: string
  value: number
}

/** 按区域统计项 */
export interface LocationItem {
  name: string
  value: number
}

/** 趋势数据点 */
export interface TrendPoint {
  date: string
  count: number
}

/** 路段时段热点 */
export interface RoadTimeHotspot {
  road: string
  time_slot: string
  count: number
}

/** 统计大屏完整响应 */
export interface StatisticsPayload {
  overview: StatisticsOverview
  violation_types: ViolationTypeItem[]
  locations: LocationItem[]
  trend?: TrendPoint[]
  road_time_hotspots?: RoadTimeHotspot[]
}
