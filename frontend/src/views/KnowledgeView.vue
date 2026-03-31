<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { api } from '../api/client'
import type { KnowledgeBase } from '../types'

const knowledgeBases = ref<KnowledgeBase[]>([])
const selectedKnowledgeBaseId = ref('')
const creating = ref(false)
const uploading = ref(false)
const uploadFile = ref<File | null>(null)
const form = reactive({
  name: '',
  description: '',
  title: '',
})

const selectedKnowledgeBase = computed(
  () => knowledgeBases.value.find((item) => item.id === selectedKnowledgeBaseId.value) || null,
)

async function loadKnowledgeBases() {
  knowledgeBases.value = await api.listKnowledgeBases()
  selectedKnowledgeBaseId.value = knowledgeBases.value[0]?.id || ''
}

async function createKnowledgeBase() {
  creating.value = true
  try {
    const knowledgeBase = await api.createKnowledgeBase({
      name: form.name,
      description: form.description,
    })
    knowledgeBases.value = [knowledgeBase, ...knowledgeBases.value]
    selectedKnowledgeBaseId.value = knowledgeBase.id
    form.name = ''
    form.description = ''
  } finally {
    creating.value = false
  }
}

async function uploadDocument() {
  if (!selectedKnowledgeBaseId.value || !uploadFile.value) {
    return
  }

  uploading.value = true
  try {
    const knowledgeBase = await api.uploadDocument(selectedKnowledgeBaseId.value, uploadFile.value, form.title)
    knowledgeBases.value = knowledgeBases.value.map((item) => (item.id === knowledgeBase.id ? knowledgeBase : item))
    uploadFile.value = null
    form.title = ''
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  void loadKnowledgeBases()
})
</script>

<template>
  <section class="workspace-view fade-up">
    <div class="split-layout split-layout--three">
      <section class="section-block">
        <header class="section-block__head">
          <span class="section-eyebrow">Libraries</span>
          <h3>资料库列表</h3>
        </header>
        <div class="stack-list">
          <button
            v-for="knowledgeBase in knowledgeBases"
            :key="knowledgeBase.id"
            class="stack-list__item"
            :class="{ 'stack-list__item--active': knowledgeBase.id === selectedKnowledgeBaseId }"
            type="button"
            @click="selectedKnowledgeBaseId = knowledgeBase.id"
          >
            <strong>{{ knowledgeBase.name }}</strong>
            <span>{{ knowledgeBase.documents.length }} documents</span>
          </button>
        </div>
      </section>

      <section class="section-block">
        <header class="section-block__head">
          <span class="section-eyebrow">Create and ingest</span>
          <h3>新建资料库</h3>
        </header>
        <form class="editor-form" @submit.prevent="createKnowledgeBase">
          <label class="field">
            <span>Name</span>
            <input v-model="form.name" type="text" placeholder="例如：产品资料库" required />
          </label>

          <label class="field">
            <span>Description</span>
            <textarea v-model="form.description" rows="4" placeholder="写清资料的来源与使用范围" />
          </label>

          <button class="button" type="submit" :disabled="creating">
            {{ creating ? '创建中...' : '创建资料库' }}
          </button>
        </form>

        <div class="divider"></div>

        <form class="editor-form" @submit.prevent="uploadDocument">
          <label class="field">
            <span>Document title</span>
            <input v-model="form.title" type="text" placeholder="不填则使用文件名" />
          </label>

          <label class="field">
            <span>File</span>
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md,.markdown"
              @change="uploadFile = ($event.target as HTMLInputElement).files?.[0] || null"
            />
          </label>

          <button class="button" type="submit" :disabled="uploading || !selectedKnowledgeBaseId || !uploadFile">
            {{ uploading ? '上传并解析中...' : '上传文档' }}
          </button>
        </form>
      </section>

      <section class="section-block">
        <header class="section-block__head">
          <span class="section-eyebrow">Documents</span>
          <h3>{{ selectedKnowledgeBase?.name || '选择一个资料库' }}</h3>
        </header>
        <div class="document-list">
          <article v-for="document in selectedKnowledgeBase?.documents || []" :key="document.id">
            <strong>{{ document.title }}</strong>
            <p>{{ document.excerpt || '暂无摘要' }}</p>
            <span>{{ document.file_name || document.source_type }} · {{ document.status }}</span>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>
