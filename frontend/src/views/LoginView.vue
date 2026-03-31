<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const mode = ref<'login' | 'register'>('login')
const loading = ref(false)

const form = reactive({
  displayName: 'Demo Operator',
  email: 'demo@aicontrol.dev',
  password: 'Demo123456!',
})

async function submit() {
  loading.value = true

  try {
    if (mode.value === 'login') {
      await authStore.login(form.email, form.password)
    } else {
      await authStore.register(form.displayName, form.email, form.password)
    }
    await router.push({ name: 'overview' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <section class="login-hero fade-up">
      <div class="login-hero__copy">
        <span class="section-eyebrow">Live workspace</span>
        <h1 class="login-hero__title">A1 Control</h1>
        <p class="login-hero__lead">
          把对话、资料和助手配置放进同一套操作台里。先看到状态，再继续推进动作。
        </p>

        <div class="login-hero__signals">
          <div>
            <span>Stream ready</span>
            <strong>FastAPI SSE</strong>
          </div>
          <div>
            <span>Knowledge layer</span>
            <strong>Upload + chunk + cite</strong>
          </div>
          <div>
            <span>Frontend system</span>
            <strong>Vue workspace shell</strong>
          </div>
        </div>
      </div>

      <div class="login-hero__visual" aria-hidden="true">
        <div class="scanline"></div>
        <div class="orb orb--amber"></div>
        <div class="orb orb--teal"></div>
        <div class="preview-grid">
          <span>Signal map</span>
          <strong>Assistants routing</strong>
          <strong>Knowledge ingestion</strong>
          <span>Live stream trace</span>
        </div>
      </div>
    </section>

    <section class="login-panel fade-up" style="animation-delay: 120ms">
      <div class="login-panel__head">
        <span class="section-eyebrow">{{ mode === 'login' ? 'Sign in' : 'Register' }}</span>
        <h2>{{ mode === 'login' ? '进入工作台' : '创建你的第一个账户' }}</h2>
      </div>

      <form class="login-form" @submit.prevent="submit">
        <label v-if="mode === 'register'" class="field">
          <span>Display name</span>
          <input v-model="form.displayName" type="text" autocomplete="name" required />
        </label>

        <label class="field">
          <span>Email</span>
          <input v-model="form.email" type="email" autocomplete="email" required />
        </label>

        <label class="field">
          <span>Password</span>
          <input v-model="form.password" type="password" autocomplete="current-password" required />
        </label>

        <p v-if="authStore.error" class="field-error">{{ authStore.error }}</p>

        <button class="button" type="submit" :disabled="loading">
          {{ loading ? '处理中...' : mode === 'login' ? '进入工作台' : '创建并进入' }}
        </button>
      </form>

      <div class="login-panel__meta">
        <p>默认演示账号已经预置完成，可以直接登录体验整套流程。</p>
        <button class="button button--ghost" type="button" @click="mode = mode === 'login' ? 'register' : 'login'">
          {{ mode === 'login' ? '切换到注册' : '切换到登录' }}
        </button>
      </div>
    </section>
  </div>
</template>
