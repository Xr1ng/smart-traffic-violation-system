/** 违章状态 */
export type ViolationStatus =
  | 'pending'        // 待处理
  | 'processed'     // 已处理
  | 'paid'           // 已缴费
  | 'appealed'       // 申诉中

/** 违章记录 */
export interface Violation {
  id: number
  plate_no: string
  violation_type: string
  location_text?: string
  violation_time: string
  status: ViolationStatus
  fine_amount?: number
  points?: number
  created_at?: string
}

/** 违章查询过滤条件 */
export interface ViolationFilter {
  plate?: string
  type?: string
  location?: string
  status?: string
  dateRange?: [string, string]
}
