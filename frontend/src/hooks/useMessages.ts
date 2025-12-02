/**
 * 消息管理 Hook
 * 管理当前会话的消息列表、发送消息等
 */
import { useState, useCallback, useEffect } from 'react'
import { message as antdMessage } from 'antd'
import type { Message } from '../api/client'
import * as api from '../api/client'

export interface LocalMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  streaming?: boolean
}

interface UseMessagesReturn {
  messages: LocalMessage[]
  loading: boolean
  streaming: boolean
  loadMessages: (sessionId: string) => Promise<void>
  sendMessage: (sessionId: string, content: string) => Promise<void>
  sendStreamMessage: (sessionId: string, content: string) => Promise<void>
  clearMessages: () => void
}

export function useMessages(): UseMessagesReturn {
  const [messages, setMessages] = useState<LocalMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)

  /**
   * 加载会话的所有消息
   */
  const loadMessages = useCallback(async (sessionId: string) => {
    if (!sessionId) return
    
    setLoading(true)
    try {
      const apiMessages = await api.getSessionMessages(sessionId)
      const localMessages: LocalMessage[] = apiMessages.map((msg) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
      }))
      setMessages(localMessages)
    } catch (error) {
      console.error('加载消息失败:', error)
      antdMessage.error('加载消息失败')
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * 发送消息（非流式）
   */
  const sendMessage = useCallback(async (
    sessionId: string,
    content: string
  ) => {
    if (!sessionId || !content.trim()) return
    
    setLoading(true)
    
    // 添加用户消息到界面
    const userMessage: LocalMessage = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    
    try {
      const response = await api.sendMessage(sessionId, content.trim())
      
      // 添加 AI 回复
      const assistantMessage: LocalMessage = {
        id: `temp-assistant-${Date.now()}`,
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('发送消息失败:', error)
      antdMessage.error('发送消息失败')
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * 发送消息（流式）
   */
  const sendStreamMessage = useCallback(async (
    sessionId: string,
    content: string
  ) => {
    if (!sessionId || !content.trim()) return
    
    setStreaming(true)
    
    // 添加用户消息到界面
    const userMessage: LocalMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    
    // 创建空的 AI 消息，用于流式更新
    const assistantMessageId = `assistant-${Date.now()}`
    const assistantMessage: LocalMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      streaming: true,
    }
    setMessages((prev) => [...prev, assistantMessage])
    
    try {
      // 流式接收 AI 回复
      for await (const chunk of api.streamMessage(sessionId, content.trim())) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: msg.content + chunk }
              : msg
          )
        )
      }
      
      // 流式完成，移除 streaming 标志
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, streaming: false }
            : msg
        )
      )
    } catch (error) {
      console.error('流式发送消息失败:', error)
      antdMessage.error('发送消息失败')
      
      // 移除失败的消息
      setMessages((prev) =>
        prev.filter((msg) => msg.id !== assistantMessageId)
      )
    } finally {
      setStreaming(false)
    }
  }, [])

  /**
   * 清空消息（切换会话时使用）
   */
  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    loading,
    streaming,
    loadMessages,
    sendMessage,
    sendStreamMessage,
    clearMessages,
  }
}

