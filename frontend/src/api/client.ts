import type {
  Assistant,
  AuthResponse,
  Conversation,
  DashboardOverview,
  KnowledgeBase,
  Message,
  StreamEvent,
  User,
} from '../types'

const API_ROOT = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const TOKEN_KEY = 'ai-assistant.token'

export class ApiError extends Error {
  public readonly status: number

  constructor(
    message: string,
    status: number,
  ) {
    super(message)
    this.status = status
  }
}

function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setAccessToken(token: string | null) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
    return
  }

  localStorage.removeItem(TOKEN_KEY)
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')

  if (!(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const token = getAccessToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    headers,
  })

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new ApiError(payload?.detail || 'Request failed.', response.status)
  }

  return (await response.json()) as T
}

export const api = {
  async login(payload: { email: string; password: string }) {
    return request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async register(payload: { email: string; password: string; display_name: string }) {
    return request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async me() {
    return request<User>('/auth/me')
  },

  async getOverview() {
    return request<DashboardOverview>('/dashboard/overview')
  },

  async listConversations() {
    return request<Conversation[]>('/conversations')
  },

  async createConversation(payload: { title: string; assistant_id?: string | null }) {
    return request<Conversation>('/conversations', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async listMessages(conversationId: string) {
    return request<Message[]>(`/conversations/${conversationId}/messages`)
  },

  async listAssistants() {
    return request<Assistant[]>('/assistants')
  },

  async createAssistant(payload: {
    name: string
    description?: string
    system_prompt: string
    provider: string
    model: string
    temperature: number
    top_p: number
    max_tokens?: number
    knowledge_base_ids: string[]
    is_default?: boolean
  }) {
    return request<Assistant>('/assistants', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async listKnowledgeBases() {
    return request<KnowledgeBase[]>('/knowledge-bases')
  },

  async createKnowledgeBase(payload: { name: string; description?: string }) {
    return request<KnowledgeBase>('/knowledge-bases', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async uploadDocument(knowledgeBaseId: string, file: File, title?: string) {
    const formData = new FormData()
    formData.append('file', file)
    if (title) {
      formData.append('title', title)
    }

    return request<KnowledgeBase>(`/knowledge-bases/${knowledgeBaseId}/documents`, {
      method: 'POST',
      body: formData,
    })
  },

  async streamConversation(
    conversationId: string,
    payload: { content: string; assistant_id?: string | null; knowledge_base_ids: string[] },
    handlers: {
      onEvent: (event: StreamEvent) => void
      onComplete: () => void
    },
  ) {
    const token = getAccessToken()
    const response = await fetch(`${API_ROOT}/conversations/${conversationId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok || !response.body) {
      const errorPayload = (await response.json().catch(() => null)) as { detail?: string } | null
      throw new ApiError(errorPayload?.detail || 'Streaming request failed.', response.status)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const packets = buffer.split('\n\n')
      buffer = packets.pop() || ''

      for (const packet of packets) {
        const line = packet
          .split('\n')
          .map((entry) => entry.trim())
          .find((entry) => entry.startsWith('data: '))

        if (!line) {
          continue
        }

        const event = JSON.parse(line.replace('data: ', '')) as StreamEvent
        handlers.onEvent(event)
      }
    }

    handlers.onComplete()
  },
}
