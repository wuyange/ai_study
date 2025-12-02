/**
 * 会话管理 Hook
 * 管理会话列表、当前会话、会话操作等
 */
import { useState, useEffect, useCallback } from 'react'
import { message as antdMessage } from 'antd'
import type { Session } from '../api/client'
import * as api from '../api/client'

interface UseSessionReturn {
  sessions: Session[]
  currentSessionId: string | null
  currentSession: Session | null
  loading: boolean
  createSession: (title?: string) => Promise<Session | null>
  switchSession: (sessionId: string) => void
  deleteSession: (sessionId: string) => Promise<boolean>
  renameSession: (sessionId: string, title: string) => Promise<boolean>
  exportSession: (sessionId: string, format: api.ExportFormat) => Promise<void>
  loadSessions: () => Promise<void>
  refreshCurrentSession: () => Promise<void>
}

export function useSession(): UseSessionReturn {
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [currentSession, setCurrentSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(false)

  /**
   * 加载会话列表
   */
  const loadSessions = useCallback(async () => {
    setLoading(true)
    try {
      const response = await api.getSessions()
      setSessions(response.sessions)
      
      // 如果当前没有选中会话，自动选中第一个
      setCurrentSessionId((prevId) => {
        if (!prevId && response.sessions.length > 0) {
          return response.sessions[0].id
        }
        return prevId
      })
    } catch (error) {
      console.error('加载会话列表失败:', error)
      antdMessage.error('加载会话列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * 创建新会话
   */
  const createSession = useCallback(async (title?: string): Promise<Session | null> => {
    console.log('[useSession] createSession called with title:', title)
    setLoading(true)
    try {
      console.log('[useSession] Calling api.createSession...')
      const newSession = await api.createSession(title)
      console.log('[useSession] API returned:', newSession)
      
      setSessions((prev) => [newSession, ...prev])
      setCurrentSessionId(newSession.id)
      setCurrentSession(newSession)
      antdMessage.success('创建新会话成功')
      
      console.log('[useSession] Session created successfully')
      return newSession
    } catch (error) {
      console.error('[useSession] 创建会话失败:', error)
      antdMessage.error('创建会话失败')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * 切换会话
   */
  const switchSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId)
    const session = sessions.find((s) => s.id === sessionId)
    setCurrentSession(session || null)
  }, [sessions])

  /**
   * 删除会话
   */
  const deleteSession = useCallback(async (sessionId: string): Promise<boolean> => {
    setLoading(true)
    try {
      await api.deleteSession(sessionId)
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
      
      // 如果删除的是当前会话，切换到第一个会话
      if (currentSessionId === sessionId) {
        const remainingSessions = sessions.filter((s) => s.id !== sessionId)
        if (remainingSessions.length > 0) {
          setCurrentSessionId(remainingSessions[0].id)
          setCurrentSession(remainingSessions[0])
        } else {
          setCurrentSessionId(null)
          setCurrentSession(null)
        }
      }
      
      antdMessage.success('删除会话成功')
      return true
    } catch (error) {
      console.error('删除会话失败:', error)
      antdMessage.error('删除会话失败')
      return false
    } finally {
      setLoading(false)
    }
  }, [currentSessionId, sessions])

  /**
   * 重命名会话
   */
  const renameSession = useCallback(async (
    sessionId: string,
    title: string
  ): Promise<boolean> => {
    setLoading(true)
    try {
      await api.updateSessionTitle(sessionId, title)
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title } : s))
      )
      
      if (currentSessionId === sessionId) {
        setCurrentSession((prev) => (prev ? { ...prev, title } : null))
      }
      
      antdMessage.success('重命名成功')
      return true
    } catch (error) {
      console.error('重命名会话失败:', error)
      antdMessage.error('重命名失败')
      return false
    } finally {
      setLoading(false)
    }
  }, [currentSessionId])

  /**
   * 导出会话
   */
  const exportSession = useCallback(async (
    sessionId: string,
    format: api.ExportFormat
  ): Promise<void> => {
    setLoading(true)
    try {
      const response = await api.exportSession(sessionId, format)
      
      // 创建下载链接
      const blob = new Blob([response.content], {
        type: format === 'json' ? 'application/json' : 'text/markdown',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = response.filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      antdMessage.success('导出成功')
    } catch (error) {
      console.error('导出会话失败:', error)
      antdMessage.error('导出失败')
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * 刷新当前会话信息
   */
  const refreshCurrentSession = useCallback(async () => {
    if (!currentSessionId) return
    
    try {
      const session = await api.getSession(currentSessionId)
      setCurrentSession(session)
      
      // 同时更新列表中的会话
      setSessions((prev) =>
        prev.map((s) => (s.id === currentSessionId ? session : s))
      )
    } catch (error) {
      console.error('刷新会话信息失败:', error)
    }
  }, [currentSessionId])

  // 初始加载会话列表
  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  // 当 currentSessionId 变化时，更新 currentSession
  useEffect(() => {
    if (currentSessionId) {
      const session = sessions.find((s) => s.id === currentSessionId)
      setCurrentSession(session || null)
    } else {
      setCurrentSession(null)
    }
  }, [currentSessionId, sessions])

  return {
    sessions,
    currentSessionId,
    currentSession,
    loading,
    createSession,
    switchSession,
    deleteSession,
    renameSession,
    exportSession,
    loadSessions,
    refreshCurrentSession,
  }
}

