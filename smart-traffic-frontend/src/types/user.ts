/** 用户角色代码 */
export type RoleCode = 'citizen' | 'reviewer' | 'admin'

/** 用户状态 */
export type UserStatus = 'active' | 'disabled'

/** 用户基本信息 */
export interface UserInfo {
  id: number
  username: string
  role_code: RoleCode
  phone?: string | null
  email?: string | null
  status?: UserStatus
  created_at?: string
}

/** 登录请求 */
export interface LoginRequest {
  username: string
  password: string
}

/** 登录响应 */
export interface LoginResponse {
  access_token: string
  token?: string
  user: UserInfo
  role_code?: RoleCode
}

/** 注册请求 */
export interface RegisterRequest {
  username: string
  password: string
  phone?: string
  email?: string
  captcha?: string
}
