<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { api } from '../api/client'
import type { Assistant, KnowledgeBase } from '../types'

const assistants = ref<Assistant[]>([])
const knowledgeBases = ref<KnowledgeBase[]>([])
const selectedAssistantId = ref<string>('')
const saving = ref(false)
const form = reactive({
  name: '',
  description: '',
  system_prompt: '你是一名结构化、冷静、可执行的 AI 助手，回答需要清晰和分点。',
  provider: 'qwen',
  model: 'qwen3.5-plus',
  temperature: 0.7,
  top_p: 1,
  max_tokens: 800,
  knowledge_base_ids: [] as string[],
})
const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'qwen', label: '千问 / 百炼' },
  { value: 'doubao', label: '豆包 / 方舟' },
]

const selectedAssistant = computed(() =>
  assistants.value.find((assistant) => assistant.id === selectedAssistantId.value) || null,
)

async function loadData() {
  const [assistantRows, knowledgeRows] = await Promise.all([api.listAssistants(), api.listKnowledgeBases()])
  assistants.value = assistantRows
  knowledgeBases.value = knowledgeRows
  selectedAssistantId.value = assistantRows[0]?.id || ''
}

async function createAssistant() {
  saving.value = true
  try {
    const assistant = await api.createAssistant({
      ...form,
      knowledge_base_ids: [...form.knowledge_base_ids],
    })
    assistants.value = [assistant, ...assistants.value]
    selectedAssistantId.value = assistant.id
    form.name = ''
    form.description = ''
    form.system_prompt = '你是一名结构化、冷静、可执行的 AI 助手，回答需要清晰和分点。'
    form.provider = 'qwen'
    form.model = 'qwen3.5-plus'
    form.temperature = 0.7
    form.top_p = 1
    form.max_tokens = 800
    form.knowledge_base_ids = []
  } finally {
    saving.value = false
  }
}

function toggleKnowledgeBase(id: string) {
  form.knowledge_base_ids = form.knowledge_base_ids.includes(id)
    ? form.knowledge_base_ids.filter((entry) => entry !== id)
    : [...form.knowledge_base_ids, id]
}

function syncModelWithProvider(provider: string) {
  if (provider === 'qwen') {
    form.model = 'qwen3.5-plus'
    return
  }

  if (provider === 'doubao') {
    form.model = 'doubao-seed-1-6-251015'
    return
  }

  form.model = 'gpt-4.1-mini'
}

onMounted(() => {
  void loadData()
})
</script>

<template>
  <section class="workspace-view fade-up">
    <div class="split-layout split-layout--three">
      <section class="section-block">
        <header class="section-block__head">
          <span class="section-eyebrow">Roster</span>
          <h3>现有助手</h3>
        </header>
        <div class="stack-list">
          <button
            v-for="assistant in assistants"
            :key="assistant.id"
            class="stack-list__item"
            :class="{ 'stack-list__item--active': assistant.id === selectedAssistantId }"
            type="button"
            @click="selectedAssistantId = assistant.id"
          >
            <strong>{{ assistant.name }}</strong>
            <span>{{ assistant.description || '未填写描述' }}</span>
          </button>
        </div>
      </section>

      <section class="section-block">
        <header class="section-block__head">
          <span class="section-eyebrow">Create</span>
          <h3>新建助手</h3>
        </header>
        <form class="editor-form" @submit.prevent="createAssistant">
          <label class="field">
            <span>Name</span>
            <input v-model="form.name" type="text" placeholder="例如：运营复盘助手" required />
          </label>

          <label class="field">
            <span>Description</span>
            <input v-model="form.description" type="text" placeholder="一句话描述它的职责" />
          </label>

          <label class="field">
            <span>System prompt</span>
            <textarea v-model="form.system_prompt" rows="7" required />
          </label>

          <div class="field-grid">
            <label class="field">
              <span>Provider</span>
              <select v-model="form.provider" @change="syncModelWithProvider(form.provider)">
                <option v-for="provider in providerOptions" :key="provider.value" :value="provider.value">
                  {{ provider.label }}
                </option>
              </select>
            </label>

            <label class="field">
              <span>Model</span>
              <input v-model="form.model" type="text" />
            </label>

            <label class="field">
              <span>Temperature</span>
              <input v-model.number="form.temperature" type="number" min="0" max="2" step="0.1" />
            </label>

            <label class="field">
              <span>Top P</span>
              <input v-model.number="form.top_p" type="number" min="0.1" max="1" step="0.1" />
            </label>

            <label class="field">
              <span>Max tokens</span>
              <input v-model.number="form.max_tokens" type="number" min="50" step="50" />
            </label>
          </div>

          <div class="picker-list">
            <button
              v-for="knowledgeBase in knowledgeBases"
              :key="knowledgeBase.id"
              class="picker-list__item"
              :class="{ 'picker-list__item--selected': form.knowledge_base_ids.includes(knowledgeBase.id) }"
              type="button"
              @click="toggleKnowledgeBase(knowledgeBase.id)"
            >
              {{ knowledgeBase.name }}
            </button>
          </div>

          <button class="button" type="submit" :disabled="saving">
            {{ saving ? '保存中...' : '创建助手' }}
          </button>
        </form>
      </section>

      <section class="section-block">
        <header class="section-block__head">
          <span class="section-eyebrow">Inspector</span>
          <h3>当前选择</h3>
        </header>
        <div v-if="selectedAssistant" class="inspector">
          <strong>{{ selectedAssistant.name }}</strong>
          <p>{{ selectedAssistant.description || '没有额外描述。' }}</p>
          <dl>
            <div>
              <dt>Provider</dt>
              <dd>{{ selectedAssistant.provider }}</dd>
            </div>
            <div>
              <dt>Model</dt>
              <dd>{{ selectedAssistant.model }}</dd>
            </div>
            <div>
              <dt>Temperature</dt>
              <dd>{{ selectedAssistant.temperature }}</dd>
            </div>
            <div>
              <dt>Knowledge</dt>
              <dd>{{ selectedAssistant.knowledge_base_ids.length }} linked</dd>
            </div>
          </dl>
          <pre>{{ selectedAssistant.system_prompt }}</pre>
        </div>
      </section>
    </div>
  </section>
</template>
