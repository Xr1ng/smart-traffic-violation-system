/** 后端标准信封响应 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 分页查询参数 */
export interface PaginationParams {
  page?: number
  page_size?: number
}

/** 分页响应 */
export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** 时间范围参数 */
export interface TimeRangeParams {
  start_time: string
  end_time: string
}

/** 构建 Payload 工具类型 */
export type NullableRecord = Record<string, unknown | null | undefined>
