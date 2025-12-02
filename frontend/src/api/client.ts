/**
 * API 客户端封装
 * 统一管理所有后端 API 调用
 */

export interface Session {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count?: number
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
}

export type ExportFormat = 'json' | 'markdown'

const API_BASE = '/api'

/**
 * 通用请求函数
 */
async function request<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `Request failed: ${response.statusText}`)
  }

  return response.json()
}

// ============= 会话管理 API =============

/**
 * 创建新会话
 */
export async function createSession(title?: string): Promise<Session> {
  return request<Session>('/sessions', {
    method: 'POST',
    body: JSON.stringify({ title: title || '新对话' }),
  })
}

/**
 * 获取所有会话列表
 */
export async function getSessions(): Promise<SessionListResponse> {
  return request<SessionListResponse>('/sessions')
}

/**
 * 获取单个会话详情
 */
export async function getSession(sessionId: string): Promise<Session> {
  return request<Session>(`/sessions/${sessionId}`)
}

/**
 * 更新会话标题
 */
export async function updateSessionTitle(
  sessionId: string,
  title: string
): Promise<{ success: boolean; message: string }> {
  return request(`/sessions/${sessionId}/title`, {
    method: 'PUT',
    body: JSON.stringify({ title }),
  })
}

/**
 * 删除会话
 */
export async function deleteSession(
  sessionId: string
): Promise<{ success: boolean; message: string }> {
  return request(`/sessions/${sessionId}`, {
    method: 'DELETE',
  })
}

/**
 * 导出会话
 */
export async function exportSession(
  sessionId: string,
  format: ExportFormat = 'json'
): Promise<{ content: string; format: string; filename: string }> {
  return request(`/sessions/${sessionId}/export?format=${format}`)
}

// ============= 消息管理 API =============

/**
 * 获取会话的所有消息
 */
export async function getSessionMessages(sessionId: string): Promise<Message[]> {
  return request<Message[]>(`/sessions/${sessionId}/messages`)
}

/**
 * 发送消息（非流式）
 */
export async function sendMessage(
  sessionId: string,
  message: string
): Promise<{ content: string; role: string }> {
  return request(`/sessions/${sessionId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

/**
 * 流式发送消息
 */
export async function* streamMessage(
  sessionId: string,
  message: string
): AsyncGenerator<string, void, unknown> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  })

  if (!response.ok) {
    throw new Error(`Stream request failed: ${response.statusText}`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('Response body is not readable')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()

          if (data === '[DONE]') {
            return
          }

          try {
            const parsed = JSON.parse(data)
            if (parsed.content) {
              yield parsed.content
            } else if (parsed.error) {
              throw new Error(parsed.error)
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', data, e)
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

/**
 * 生成会话标题
 */
export async function generateSessionTitle(
  sessionId: string
): Promise<{ success: boolean; title: string }> {
  return request(`/sessions/${sessionId}/generate-title`, {
    method: 'POST',
  })
}

// ============= 健康检查 API =============

/**
 * 健康检查
 */
export async function healthCheck(): Promise<{
  status: string
  service: string
  autogen_initialized: boolean
  version: string
}> {
  return request('/health')
}

