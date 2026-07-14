import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getUserInfo } from '@/api/auth'
import type { LoginResponse, RoleCode, UserInfo } from '@/types'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)
  const role = ref<RoleCode | ''>(localStorage.getItem('role') as RoleCode | '' || '')

  const homePath = computed<string>(() => {
    if (role.value === 'citizen') return '/citizen/home'
    if (role.value === 'reviewer') return '/review/workbench'
    return '/admin/stats'
  })

  async function login(credentials: { username: string; password: string }) {
    const res = await loginApi(credentials)
    const data: LoginResponse = res.data
    token.value = data.access_token || data.token || ''
    role.value = (data.user?.role_code || data.role_code || 'citizen') as RoleCode
    userInfo.value = data.user ?? data
    localStorage.setItem('token', token.value)
    localStorage.setItem('role', role.value)
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    return res
  }

  async function restoreLoginState() {
    if (!token.value) return
    try {
      const res = await getUserInfo()
      userInfo.value = res.data as UserInfo
      role.value = (res.data as UserInfo).role_code
      localStorage.setItem('role', role.value)
      localStorage.setItem('userInfo', JSON.stringify(res.data))
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    role.value = ''
    localStorage.clear()
  }

  return { token, userInfo, role, homePath, login, restoreLoginState, logout }
})
