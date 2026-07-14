import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getUserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  const role = ref(localStorage.getItem('role') || '')

  // v2.0 角色: citizen(市民) / reviewer(审核员) / admin(超级管理员)
  const homePath = computed(() => {
    if (role.value === 'citizen') return '/citizen/home'
    if (role.value === 'reviewer') return '/review/workbench'
    return '/admin/stats'
  })

  async function login(credentials) {
    const res = await loginApi(credentials)
    // 后端响应: { access_token, user: { id, username, role_code } }
    const data = res.data
    token.value = data.access_token || data.token
    role.value = data.user?.role_code || data.role_code
    userInfo.value = data.user || data
    localStorage.setItem('token', token.value)
    localStorage.setItem('role', role.value)
    return res
  }

  async function restoreLoginState() {
    if (!token.value) return
    try {
      const res = await getUserInfo()
      userInfo.value = res.data
      role.value = res.data.role_code
      localStorage.setItem('role', res.data.role_code)
      localStorage.setItem('userInfo', JSON.stringify(res.data))
    } catch {
      logout()
    }
  }

  function setUserInfo(info) {
    userInfo.value = info
    if (info?.role_code) {
      role.value = info.role_code
      localStorage.setItem('role', info.role_code)
    }
    localStorage.setItem('userInfo', JSON.stringify(info))
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    role.value = ''
    localStorage.clear()
  }

  return { token, userInfo, role, homePath, login, restoreLoginState, setUserInfo, logout }
})
