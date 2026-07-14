import request from './request'
import type { ApiResponse } from '@/types'
import type { LoginResponse, UserInfo, LoginRequest, RegisterRequest } from '@/types'

/** 认证 API — 对齐 API接口规范文档 v2.0 §2 */
export const login = (data: LoginRequest) =>
  request.post<ApiResponse<LoginResponse>>('/auth/login', data)

export const register = (data: RegisterRequest) =>
  request.post<ApiResponse<unknown>>('/auth/register', data)

export const getUserInfo = () =>
  request.get<ApiResponse<UserInfo>>('/auth/me')

export const updateProfile = (data: Partial<UserInfo>) =>
  request.put<ApiResponse<UserInfo>>('/auth/profile', data)

export const changePassword = (data: { old_password: string; new_password: string }) =>
  request.put<ApiResponse<unknown>>('/auth/password', data)

export const getMenus = () =>
  request.get<ApiResponse<unknown>>('/permissions/menus')

/** 注册 — 发送邮箱验证码 */
export const registerSendCode = (data: { email: string }) =>
  request.post<ApiResponse<unknown>>('/auth/register/send-code', data)

/** 忘记密码 — 验证身份并发送验证码 */
export const forgotPasswordVerify = (data: { username: string; email: string }) =>
  request.post<ApiResponse<{ token: string }>>('/auth/forgot-password/verify', data)

/** 忘记密码 — 重置密码 */
export const forgotPasswordReset = (data: { username: string; email: string; code: string; new_password: string }) =>
  request.post<ApiResponse<unknown>>('/auth/forgot-password/reset', data)
