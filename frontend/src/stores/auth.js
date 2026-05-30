import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoggedIn = computed(() => !!user.value)

  async function check() {
    try {
      const res = await api.get('/api/auth/me')
      user.value = res.data
    } catch {
      user.value = null
    }
    return user.value
  }

  async function login(studentId, password) {
    const res = await api.post('/api/auth/login', {
      student_id: studentId,
      password,
    })
    user.value = res.data
    return res
  }

  async function logout() {
    try {
      await api.post('/api/auth/logout')
    } catch { /* ignore */ }
    user.value = null
  }

  /** 刷新余额 */
  async function refreshBalance() {
    if (!user.value) return
    try {
      const res = await api.get('/api/auth/me')
      user.value.edu_balance = res.data.edu_balance
    } catch { /* ignore */ }
  }

  return { user, isLoggedIn, check, login, logout, refreshBalance }
})
