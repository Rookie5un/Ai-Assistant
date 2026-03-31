import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { api, ApiError, setAccessToken } from '../api/client'
import type { User } from '../types'

const TOKEN_KEY = 'ai-assistant.token'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const ready = ref(false)
  const error = ref('')

  const isAuthenticated = computed(() => Boolean(token.value && user.value))

  async function bootstrap() {
    if (!token.value) {
      ready.value = true
      return
    }

    try {
      user.value = await api.me()
    } catch {
      logout()
    } finally {
      ready.value = true
    }
  }

  async function login(email: string, password: string) {
    error.value = ''

    try {
      const response = await api.login({ email, password })
      token.value = response.access_token
      user.value = response.user
      setAccessToken(response.access_token)
    } catch (caught) {
      if (caught instanceof ApiError) {
        error.value = caught.message
      } else {
        error.value = 'Unable to sign in right now.'
      }
      throw caught
    }
  }

  async function register(displayName: string, email: string, password: string) {
    error.value = ''

    try {
      const response = await api.register({ display_name: displayName, email, password })
      token.value = response.access_token
      user.value = response.user
      setAccessToken(response.access_token)
    } catch (caught) {
      if (caught instanceof ApiError) {
        error.value = caught.message
      } else {
        error.value = 'Unable to create account right now.'
      }
      throw caught
    }
  }

  function logout() {
    token.value = null
    user.value = null
    error.value = ''
    setAccessToken(null)
  }

  return {
    user,
    token,
    ready,
    error,
    isAuthenticated,
    bootstrap,
    login,
    logout,
    register,
  }
})
