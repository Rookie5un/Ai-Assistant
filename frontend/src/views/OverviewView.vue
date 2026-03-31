<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api } from '../api/client'
import type { DashboardOverview } from '../types'

const loading = ref(true)
const overview = ref<DashboardOverview | null>(null)

async function loadOverview() {
  loading.value = true
  try {
    overview.value = await api.getOverview()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadOverview()
})
</script>

<template>
  <section class="workspace-view fade-up">
    <div class="metric-strip">
      <template v-if="overview">
        <article v-for="metric in overview.metrics" :key="metric.label" class="metric-strip__item">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
          <p>{{ metric.detail }}</p>
        </article>
      </template>
      <p v-else-if="loading">正在整理当前工作台状态...</p>
    </div>

    <div class="split-layout split-layout--overview">
      <section class="section-block">
        <header class="section-block__head">
          <span class="section-eyebrow">Assistant status</span>
          <h3>当前激活策略</h3>
        </header>
        <ul class="line-list">
          <li v-for="item in overview?.active_assistants || []" :key="item">{{ item }}</li>
        </ul>
      </section>

      <section class="section-block">
        <header class="section-block__head">
          <span class="section-eyebrow">Ingestion queue</span>
          <h3>建议补齐的资料</h3>
        </header>
        <ul class="line-list">
          <li v-for="item in overview?.pending_documents || []" :key="item">{{ item }}</li>
        </ul>
      </section>
    </div>

    <section class="section-block">
      <header class="section-block__head">
        <span class="section-eyebrow">Activity</span>
        <h3>最近动作</h3>
      </header>
      <div class="activity-list">
        <article v-for="item in overview?.activity || []" :key="`${item.label}-${item.timestamp}`">
          <strong>{{ item.label }}</strong>
          <p>{{ item.detail }}</p>
          <span>{{ item.timestamp }}</span>
        </article>
      </div>
    </section>
  </section>
</template>
