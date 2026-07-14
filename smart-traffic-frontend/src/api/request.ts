import axios, {
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import type { ApiResponse } from '@/types'

/** 原始后端响应，可能为标准信封或裸 Pydantic 数据 */
type RawResponse = unknown

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// 请求拦截器 —— 自动携带 token
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error),
)

// 响应拦截器 —— 统一处理错误
request.interceptors.response.use(
  (response: AxiosResponse<RawResponse>) => {
    const raw = response.data
    // 后端返回裸 Pydantic（无 {code, message, data} 信封），包一层
    if (typeof raw === 'object' && raw !== null && !('code' in (raw as object))) {
      return { code: response.status, message: 'ok', data: raw } as unknown as ApiResponse
    }
    const envelope = raw as ApiResponse
    if (envelope.code === 401) {
      localStorage.clear()
      router.push('/login')
      return Promise.reject(new Error('登录已过期'))
    }
    return envelope as unknown as AxiosResponse
  },
  error => {
    if (error.response) {
      const { status, data, config } = error.response as AxiosResponse<{ detail?: string; message?: string }>
      switch (status) {
        case 401:
          // 登录接口的 401 是"用户名或密码错误"，不要清除 token 或跳转
          if (config.url?.endsWith('/auth/login')) {
            ElMessage.error(data?.detail || '用户名或密码错误')
          } else {
            localStorage.clear()
            router.push('/login')
            ElMessage.error('登录已过期，请重新登录')
          }
          break
        case 403:
          ElMessage.error('没有操作权限')
          break
        case 500:
          ElMessage.error('服务器错误，请稍后重试')
          break
        default:
          ElMessage.error(data?.detail || data?.message || '请求失败')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  },
)

export default request
