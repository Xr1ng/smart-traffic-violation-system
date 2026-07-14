/** 车辆信息 */
export interface Vehicle {
  id: number
  plate_no: string
  owner_id: number | null
  owner_name?: string
  vehicle_type?: string | null
  color?: string | null
  created_at?: string
}

/** 新增/编辑车辆请求体 */
export interface VehiclePayload {
  plate_no: string
  owner_id: number | null
  vehicle_type?: string | null
  color?: string | null
}

/** 车辆查询参数 */
export interface VehicleQuery {
  page?: number
  page_size?: number
  plate_no?: string
}
