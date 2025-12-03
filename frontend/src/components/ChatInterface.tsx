/**
 * 聊天界面组件（多会话版本）
 * 支持会话管理、历史消息、流式输出等
 */
import { useState, useRef, useEffect } from 'react'
import { Bubble, Sender, XProvider } from '@ant-design/x'
import { UserOutlined, RobotOutlined, MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons'
import { Button, Avatar, Empty, Spin } from 'antd'
import { SessionSidebar } from './SessionSidebar'
import { RenameModal, ExportModal, showDeleteConfirm } from './SessionActions'
import { useSession } from '../hooks/useSession'
import { useMessages } from '../hooks/useMessages'
import * as api from '../api/client'
import './ChatInterface.css'

const ChatInterface = () => {
  const [inputValue, setInputValue] = useState('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const chatBodyRef = useRef<HTMLDivElement>(null)
  
  // 重命名对话框状态
  const [renameVisible, setRenameVisible] = useState(false)
  const [renamingSessionId, setRenamingSessionId] = useState<string>('')
  const [renamingCurrentTitle, setRenamingCurrentTitle] = useState('')
  
  // 导出对话框状态
  const [exportVisible, setExportVisible] = useState(false)
  const [exportingSessionId, setExportingSessionId] = useState<string>('')

  // 使用自定义 Hooks
  const {
    sessions,
    currentSessionId,
    currentSession,
    loading: sessionLoading,
    createSession,
    switchSession,
    deleteSession,
    renameSession,
    exportSession,
    refreshCurrentSession,
  } = useSession()

  const {
    messages,
    loading: messageLoading,
    streaming,
    loadMessages,
    sendStreamMessage,
    clearMessages,
  } = useMessages()

  // 当切换会话时，加载该会话的消息
  useEffect(() => {
    if (currentSessionId) {
      clearMessages()
      loadMessages(currentSessionId)
    }
  }, [currentSessionId, clearMessages, loadMessages])

  // 自动滚动到底部
  useEffect(() => {
    if (chatBodyRef.current) {
      setTimeout(() => {
        chatBodyRef.current?.scrollTo({
          top: chatBodyRef.current.scrollHeight,
          behavior: 'smooth'
        })
      }, 100)
    }
  }, [messages])

  /**
   * 创建新会话
   */
  const handleCreateSession = async () => {
    console.log('[ChatInterface] handleCreateSession called')
    try {
      const newSession = await createSession('新对话')
      console.log('[ChatInterface] createSession returned:', newSession)
      if (newSession) {
        clearMessages()
      }
    } catch (error) {
      console.error('[ChatInterface] handleCreateSession error:', error)
    }
  }

  /**
   * 选择会话
   */
  const handleSelectSession = (sessionId: string) => {
    switchSession(sessionId)
  }

  /**
   * 显示重命名对话框
   */
  const handleShowRename = (sessionId: string, currentTitle: string) => {
    setRenamingSessionId(sessionId)
    setRenamingCurrentTitle(currentTitle)
    setRenameVisible(true)
  }

  /**
   * 执行重命名
   */
  const handleRename = async (newTitle: string) => {
    const success = await renameSession(renamingSessionId, newTitle)
    if (success) {
      setRenameVisible(false)
    }
  }

  /**
   * 显示删除确认
   */
  const handleShowDelete = (sessionId: string) => {
    const session = sessions.find((s) => s.id === sessionId)
    if (session) {
      showDeleteConfirm(session.title, () => handleDelete(sessionId))
    }
  }

  /**
   * 执行删除
   */
  const handleDelete = async (sessionId: string) => {
    await deleteSession(sessionId)
  }

  /**
   * 显示导出对话框
   */
  const handleShowExport = (sessionId: string) => {
    setExportingSessionId(sessionId)
    setExportVisible(true)
  }

  /**
   * 执行导出
   */
  const handleExport = async (format: api.ExportFormat) => {
    await exportSession(exportingSessionId, format)
    setExportVisible(false)
  }

  /**
   * 发送消息
   */
  const handleSend = async (message: string) => {
    if (!message.trim() || streaming || messageLoading) return
    
    // 如果没有当前会话，先创建一个
    let sessionId = currentSessionId
    if (!sessionId) {
      const newSession = await createSession('新对话')
      if (!newSession) return
      sessionId = newSession.id
    }
    
    // 检查是否是第一条消息
    const isFirstMessage = messages.length === 0
    
    // 发送消息
    await sendStreamMessage(sessionId, message.trim())
    
    // 如果是第一条消息，自动生成标题
    if (isFirstMessage && sessionId) {
      try {
        const result = await api.generateSessionTitle(sessionId)
        if (result.success) {
          // 刷新当前会话信息以更新标题
          await refreshCurrentSession()
        }
      } catch (error) {
        console.error('自动生成标题失败:', error)
      }
    }
    
    setInputValue('')
  }

  // 转换消息为 Bubble.List 格式
  const bubbleItems = messages.map(msg => ({
    key: msg.id,
    role: msg.role,
    content: msg.content,
    avatar: msg.role === 'user' ? (
      <Avatar icon={<UserOutlined />} style={{ background: '#667eea' }} />
    ) : (
      <Avatar icon={<RobotOutlined />} style={{ background: '#764ba2' }} />
    ),
    placement: msg.role === 'user' ? 'end' : 'start',
    streaming: msg.streaming,
    typing: msg.streaming ? { step: 3, interval: 30 } : false,
  }))

  return (
    <XProvider>
      <div className="multi-session-container">
        {/* 侧边栏 */}
        {!sidebarCollapsed && (
          <SessionSidebar
            sessions={sessions}
            currentSessionId={currentSessionId}
            loading={sessionLoading}
            onCreateSession={handleCreateSession}
            onSelectSession={handleSelectSession}
            onRenameSession={handleShowRename}
            onDeleteSession={handleShowDelete}
            onExportSession={handleShowExport}
          />
        )}

        {/* 主聊天区域 */}
        <div className="chat-main-area">
          <div className="chat-container">
            {/* 顶部标题栏 */}
            <div className="chat-header">
              <div className="chat-title">
                <Button
                  type="text"
                  icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                  onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                  style={{ color: 'white', marginRight: 12 }}
                />
                <RobotOutlined style={{ fontSize: 24, marginRight: 12 }} />
                <span>{currentSession?.title || 'AI 助手'}</span>
              </div>
            </div>
            
            {/* 消息列表区域 */}
            <div className="chat-body" ref={chatBodyRef}>
              {!currentSessionId ? (
                <Empty
                  description="请选择或创建一个会话开始对话"
                  style={{ marginTop: 100 }}
                />
              ) : messageLoading && messages.length === 0 ? (
                <div style={{ textAlign: 'center', marginTop: 100 }}>
                  <Spin size="large" />
                  <div style={{ marginTop: 16, color: '#999' }}>加载消息中...</div>
                </div>
              ) : messages.length === 0 ? (
                <Empty
                  description="暂无消息，开始对话吧"
                  style={{ marginTop: 100 }}
                />
              ) : (
                <div className="bubble-list">
                  {messages.map(msg => (
                    <Bubble
                      key={msg.id}
                      content={msg.content}
                      avatar={
                        msg.role === 'user' ? (
                          <Avatar icon={<UserOutlined />} style={{ background: '#667eea' }} />
                        ) : (
                          <Avatar icon={<RobotOutlined />} style={{ background: '#764ba2' }} />
                        )
                      }
                      placement={msg.role === 'user' ? 'end' : 'start'}
                      typing={msg.streaming ? { step: 3, interval: 30 } : undefined}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* 输入区域 */}
            <div className="chat-footer">
              <Sender
                value={inputValue}
                onChange={setInputValue}
                onSubmit={handleSend}
                placeholder={currentSessionId ? "输入消息..." : "请先创建或选择会话"}
                loading={streaming}
                disabled={!currentSessionId}
                allowSpeech={false}
                style={{
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                }}
              />
            </div>
          </div>
        </div>

        {/* 重命名对话框 */}
        <RenameModal
          visible={renameVisible}
          currentTitle={renamingCurrentTitle}
          loading={sessionLoading}
          onOk={handleRename}
          onCancel={() => setRenameVisible(false)}
        />

        {/* 导出对话框 */}
        <ExportModal
          visible={exportVisible}
          loading={sessionLoading}
          onOk={handleExport}
          onCancel={() => setExportVisible(false)}
        />
      </div>
    </XProvider>
  )
}

export default ChatInterface
