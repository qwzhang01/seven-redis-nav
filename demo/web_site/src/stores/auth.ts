import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface UserInfo {
  id: string
  username: string
  email: string
  avatar?: string
  role: 'user' | 'admin'
  createdAt: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('qm_token'))
  const user = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function init() {
    const saved = localStorage.getItem('qm_user')
    if (saved && token.value) {
      try {
        user.value = JSON.parse(saved)
      } catch {
        logout()
      }
    }
  }

  function login(email: string, _password: string) {
    const mockUser: UserInfo = {
      id: 'user-1',
      username: email.split('@')[0],
      email,
      role: email.includes('admin') ? 'admin' : 'user',
      createdAt: new Date().toISOString(),
    }
    const mockToken = 'qm_' + Math.random().toString(36).slice(2)
    token.value = mockToken
    user.value = mockUser
    localStorage.setItem('qm_token', mockToken)
    localStorage.setItem('qm_user', JSON.stringify(mockUser))
    return mockUser
  }

  function register(username: string, email: string, _password: string) {
    const mockUser: UserInfo = {
      id: 'user-' + Date.now(),
      username,
      email,
      role: 'user',
      createdAt: new Date().toISOString(),
    }
    const mockToken = 'qm_' + Math.random().toString(36).slice(2)
    token.value = mockToken
    user.value = mockUser
    localStorage.setItem('qm_token', mockToken)
    localStorage.setItem('qm_user', JSON.stringify(mockUser))
    return mockUser
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('qm_token')
    localStorage.removeItem('qm_user')
  }

  init()

  return { token, user, isLoggedIn, isAdmin, login, register, logout }
})
