<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navigation = [
  { label: 'Overview', description: '状态与节奏', to: '/app/overview' },
  { label: 'Chat', description: '多轮对话与流式输出', to: '/app/chat' },
  { label: 'Assistants', description: '助手角色与模型', to: '/app/assistants' },
  { label: 'Knowledge', description: '资料库与文件处理', to: '/app/knowledge' },
]

const title = computed(() => String(route.meta.title || 'Workspace'))
const eyebrow = computed(() => String(route.meta.eyebrow || 'Ai Assistant Web'))

function signOut() {
  authStore.logout()
  void router.push({ name: 'login' })
}
</script>

<template>
  <div class="shell">
    <aside class="shell__nav">
      <div class="brand-lockup">
        <span class="brand-lockup__eyebrow">Ai Assistant Web</span>
        <h1 class="brand-lockup__title">A1 Control</h1>
        <p class="brand-lockup__copy">
          面向知识工作与资料检索的 AI 操作台。保持输入、上下文与知识库在同一条工作线上。
        </p>
      </div>

      <nav class="nav-list" aria-label="Primary">
        <RouterLink
          v-for="item in navigation"
          :key="item.to"
          :to="item.to"
          class="nav-list__item"
          active-class="nav-list__item--active"
        >
          <span>{{ item.label }}</span>
          <small>{{ item.description }}</small>
        </RouterLink>
      </nav>

      <div class="nav-footer">
        <span class="nav-footer__label">Signed in as</span>
        <strong>{{ authStore.user?.display_name || 'Operator' }}</strong>
        <span>{{ authStore.user?.email }}</span>
        <button class="button button--ghost" type="button" @click="signOut">退出当前会话</button>
      </div>
    </aside>

    <div class="shell__main">
      <header class="shell__header">
        <div>
          <span class="section-eyebrow">{{ eyebrow }}</span>
          <h2 class="section-title">{{ title }}</h2>
        </div>

        <div class="shell__header-copy">
          <span>Demo account available</span>
          <strong>demo@aicontrol.dev</strong>
        </div>
      </header>

      <main class="shell__content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
