/**
 * 会话侧边栏组件
 * 显示会话列表、新建会话按钮、会话操作等
 */
import { useState } from 'react'
import { Button, Dropdown, Typography, Empty } from 'antd'
import {
  PlusOutlined,
  MessageOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import type { Session } from '../api/client'
import './SessionSidebar.css'

const { Text } = Typography

interface SessionSidebarProps {
  sessions: Session[]
  currentSessionId: string | null
  loading: boolean
  onCreateSession: () => void
  onSelectSession: (sessionId: string) => void
  onRenameSession: (sessionId: string, currentTitle: string) => void
  onDeleteSession: (sessionId: string) => void
  onExportSession: (sessionId: string) => void
}

export function SessionSidebar({
  sessions,
  currentSessionId,
  loading,
  onCreateSession,
  onSelectSession,
  onRenameSession,
  onDeleteSession,
  onExportSession,
}: SessionSidebarProps) {
  const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null)

  /**
   * 格式化时间显示
   */
  const formatTime = (dateStr: string): string => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins}分钟前`
    if (diffHours < 24) return `${diffHours}小时前`
    if (diffDays < 7) return `${diffDays}天前`
    
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
    })
  }

  /**
   * 获取会话操作菜单项
   */
  const getMenuItems = (session: Session): MenuProps['items'] => [
    {
      key: 'rename',
      label: '重命名',
      icon: <EditOutlined />,
      onClick: () => onRenameSession(session.id, session.title),
    },
    {
      key: 'export',
      label: '导出',
      icon: <DownloadOutlined />,
      onClick: () => onExportSession(session.id),
    },
    {
      type: 'divider',
    },
    {
      key: 'delete',
      label: '删除',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: () => onDeleteSession(session.id),
    },
  ]

  return (
    <div className="session-sidebar">
      {/* 新建会话按钮 */}
      <div className="sidebar-header">
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={(e) => {
            e.preventDefault()
            console.log('[SessionSidebar] 新建会话按钮被点击')
            onCreateSession()
          }}
          loading={loading}
          block
          size="large"
          className="new-session-btn"
        >
          新建会话
        </Button>
      </div>

      {/* 会话列表 */}
      <div className="sidebar-content">
        {sessions.length === 0 ? (
          <Empty
            description="暂无会话"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{ marginTop: 60 }}
          />
        ) : (
          <div className="session-list">
            {sessions.map((session) => {
              const isActive = session.id === currentSessionId
              const isHovered = session.id === hoveredSessionId

              return (
                <div
                  key={session.id}
                  className={`session-item ${isActive ? 'active' : ''}`}
                  onMouseEnter={() => setHoveredSessionId(session.id)}
                  onMouseLeave={() => setHoveredSessionId(null)}
                  onClick={() => onSelectSession(session.id)}
                >
                  <div className="session-item-content">
                    <div className="session-item-header">
                      <MessageOutlined className="session-icon" />
                      <Text
                        ellipsis
                        className="session-title"
                        title={session.title}
                      >
                        {session.title}
                      </Text>
                      
                      {/* 操作按钮（悬停时显示） */}
                      {isHovered && (
                        <Dropdown
                          menu={{ items: getMenuItems(session) }}
                          trigger={['click']}
                          placement="bottomRight"
                        >
                          <Button
                            type="text"
                            icon={<MoreOutlined />}
                            size="small"
                            className="session-action-btn"
                            onClick={(e) => e.stopPropagation()}
                          />
                        </Dropdown>
                      )}
                    </div>
                    
                    <div className="session-item-footer">
                      <Text type="secondary" className="session-time">
                        {formatTime(session.updated_at)}
                      </Text>
                      {session.message_count !== undefined && session.message_count > 0 && (
                        <>
                          <span className="session-divider">·</span>
                          <Text type="secondary" className="session-count">
                            {session.message_count} 条消息
                          </Text>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

