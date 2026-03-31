<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { ApiError, api } from '../api/client'
import type { Assistant, Conversation, KnowledgeBase, Message, StreamEvent } from '../types'

const assistants = ref<Assistant[]>([])
const conversations = ref<Conversation[]>([])
const messages = ref<Message[]>([])
const knowledgeBases = ref<KnowledgeBase[]>([])
const activeConversationId = ref('')
const selectedAssistantId = ref('')
const sending = ref(false)
const streamCitations = ref<Array<{ title: string; snippet: string }>>([])
const composer = reactive({
  content: '',
})

const activeAssistant = computed(
  () => assistants.value.find((assistant) => assistant.id === selectedAssistantId.value) || assistants.value[0] || null,
)

const activeConversation = computed(
  () => conversations.value.find((conversation) => conversation.id === activeConversationId.value) || null,
)

const activeKnowledgeBaseIds = computed(() => activeAssistant.value?.knowledge_base_ids || [])

async function bootstrapChat() {
  const [assistantRows, conversationRows, knowledgeRows] = await Promise.all([
    api.listAssistants(),
    api.listConversations(),
    api.listKnowledgeBases(),
  ])

  assistants.value = assistantRows
  knowledgeBases.value = knowledgeRows
  selectedAssistantId.value = assistantRows.find((assistant) => assistant.is_default)?.id || assistantRows[0]?.id || ''
  conversations.value = conversationRows

  if (!conversationRows.length) {
    const created = await api.createConversation({
      title: '新会话',
      assistant_id: selectedAssistantId.value || null,
    })
    conversations.value = [created]
  }

  activeConversationId.value = conversations.value[0]?.id || ''
}

async function loadMessages(conversationId: string) {
  if (!conversationId) {
    return
  }

  messages.value = await api.listMessages(conversationId)
  const lastAssistantMessage = [...messages.value].reverse().find((message) => message.role === 'assistant')
  streamCitations.value = (lastAssistantMessage?.metadata_json.citations as Array<{ title: string; snippet: string }>) || []
}

async function createConversation() {
  const created = await api.createConversation({
    title: '新会话',
    assistant_id: selectedAssistantId.value || null,
  })
  conversations.value = [created, ...conversations.value]
  activeConversationId.value = created.id
  messages.value = []
}

async function sendMessage() {
  if (!composer.content.trim() || sending.value) {
    return
  }

  let conversationId = activeConversationId.value
  if (!conversationId) {
    await createConversation()
    conversationId = activeConversationId.value
  }

  const content = composer.content.trim()
  composer.content = ''
  sending.value = true
  streamCitations.value = []

  const localUserMessage: Message = {
    id: `local-user-${Date.now()}`,
    role: 'user',
    content,
    status: 'completed',
    created_at: new Date().toISOString(),
    model: null,
    metadata_json: {},
  }

  const localAssistantMessage: Message = {
    id: `local-assistant-${Date.now()}`,
    role: 'assistant',
    content: '',
    status: 'streaming',
    created_at: new Date().toISOString(),
    model: activeAssistant.value?.model || null,
    metadata_json: { citations: [] },
  }

  messages.value = [...messages.value, localUserMessage, localAssistantMessage]

  try {
    await api.streamConversation(
      conversationId,
      {
        content,
        assistant_id: selectedAssistantId.value || null,
        knowledge_base_ids: activeKnowledgeBaseIds.value,
      },
      {
        onEvent(event: StreamEvent) {
          if (event.type === 'meta') {
            streamCitations.value = event.citations || []
            localAssistantMessage.metadata_json = {
              citations: event.citations || [],
            }
          }

          if (event.type === 'delta') {
            localAssistantMessage.content += event.delta || ''
          }

          if (event.type === 'done') {
            localAssistantMessage.status = 'completed'
          }
        },
        onComplete() {
          localAssistantMessage.status = 'completed'
        },
      },
    )

    conversations.value = await api.listConversations()
    await loadMessages(conversationId)
  } catch (caught) {
    localAssistantMessage.status = 'failed'
    if (caught instanceof ApiError) {
      localAssistantMessage.content = `模型调用失败：${caught.message}`
    } else {
      localAssistantMessage.content = '模型调用失败：服务暂时不可用，请检查后端配置。'
    }
  } finally {
    sending.value = false
  }
}

watch(activeConversationId, (conversationId) => {
  if (conversationId) {
    void loadMessages(conversationId)
  }
})

onMounted(() => {
  void bootstrapChat()
})
</script>

<template>
  <section class="workspace-view fade-up chat-workspace">
    <aside class="rail-panel">
      <header class="rail-panel__head">
        <span class="section-eyebrow">Threads</span>
        <h3>会话列表</h3>
        <button class="button button--ghost" type="button" @click="createConversation">新建会话</button>
      </header>

      <div class="stack-list">
        <button
          v-for="conversation in conversations"
          :key="conversation.id"
          class="stack-list__item"
          :class="{ 'stack-list__item--active': conversation.id === activeConversationId }"
          type="button"
          @click="activeConversationId = conversation.id"
        >
          <strong>{{ conversation.title }}</strong>
          <span>{{ conversation.summary || '等待消息' }}</span>
        </button>
      </div>
    </aside>

    <div class="chat-surface">
      <header class="chat-surface__head">
        <div>
          <span class="section-eyebrow">Conversation</span>
          <h3>{{ activeConversation?.title || '新会话' }}</h3>
        </div>

        <label class="inline-field">
          <span>Assistant</span>
          <select v-model="selectedAssistantId">
            <option v-for="assistant in assistants" :key="assistant.id" :value="assistant.id">
              {{ assistant.name }}
            </option>
          </select>
        </label>
      </header>

      <div class="message-thread">
        <article v-for="message in messages" :key="message.id" class="message-thread__item" :data-role="message.role">
          <span>{{ message.role === 'assistant' ? activeAssistant?.name || 'Assistant' : 'You' }}</span>
          <p>{{ message.content }}</p>
        </article>
      </div>

      <form class="composer" @submit.prevent="sendMessage">
        <textarea
          v-model="composer.content"
          rows="4"
          placeholder="输入你的问题、目标输出格式，或让助手基于资料继续回答。"
        />
        <div class="composer__actions">
          <span>Linked knowledge: {{ activeKnowledgeBaseIds.length }}</span>
          <button class="button" type="submit" :disabled="sending">
            {{ sending ? '生成中...' : '发送并流式返回' }}
          </button>
        </div>
      </form>
    </div>

    <aside class="rail-panel">
      <header class="rail-panel__head">
        <span class="section-eyebrow">Inspector</span>
        <h3>上下文信息</h3>
      </header>

      <div class="inspector">
        <strong>{{ activeAssistant?.name || '未选择助手' }}</strong>
        <p>{{ activeAssistant?.description || '这个助手还没有补充说明。' }}</p>
        <dl>
          <div>
            <dt>Provider</dt>
            <dd>{{ activeAssistant?.provider || 'openai' }}</dd>
          </div>
          <div>
            <dt>Prompt mode</dt>
            <dd>{{ activeAssistant?.model || 'gpt-4.1-mini' }}</dd>
          </div>
          <div>
            <dt>Knowledge links</dt>
            <dd>{{ activeKnowledgeBaseIds.length }}</dd>
          </div>
          <div>
            <dt>Available libraries</dt>
            <dd>{{ knowledgeBases.length }}</dd>
          </div>
        </dl>
        <pre>{{ activeAssistant?.system_prompt || '选择助手后这里会显示系统提示词。' }}</pre>
      </div>

      <div class="divider"></div>

      <div class="citation-list">
        <span class="section-eyebrow">Citations</span>
        <article v-for="citation in streamCitations" :key="`${citation.title}-${citation.snippet}`">
          <strong>{{ citation.title }}</strong>
          <p>{{ citation.snippet }}</p>
        </article>
        <p v-if="!streamCitations.length">当前回复还没有引用命中的资料片段。</p>
      </div>
    </aside>
  </section>
</template>
