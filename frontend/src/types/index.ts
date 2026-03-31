export interface User {
  id: string
  email: string
  display_name: string
  role: string
  last_login_at?: string | null
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface MetricItem {
  label: string
  value: string
  detail: string
}

export interface ActivityItem {
  label: string
  detail: string
  timestamp: string
}

export interface DashboardOverview {
  metrics: MetricItem[]
  active_assistants: string[]
  pending_documents: string[]
  activity: ActivityItem[]
}

export interface Conversation {
  id: string
  title: string
  summary?: string | null
  assistant_id?: string | null
  pinned: boolean
  archived: boolean
  last_message_at?: string | null
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  status: string
  model?: string | null
  created_at: string
  metadata_json: Record<string, unknown>
}

export interface Assistant {
  id: string
  name: string
  description?: string | null
  system_prompt: string
  provider: string
  model: string
  temperature: number
  top_p: number
  max_tokens?: number | null
  is_default: boolean
  visibility: string
  knowledge_base_ids: string[]
  created_at: string
  updated_at: string
}

export interface DocumentItem {
  id: string
  title: string
  source_type: string
  file_name?: string | null
  status: string
  excerpt?: string | null
  created_at: string
}

export interface KnowledgeBase {
  id: string
  name: string
  description?: string | null
  status: string
  embedding_model: string
  created_at: string
  updated_at: string
  documents: DocumentItem[]
}

export interface StreamEvent {
  type: 'meta' | 'delta' | 'done'
  citations?: Array<{ title: string; snippet: string }>
  delta?: string
}
