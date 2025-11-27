import { useState, useRef, useEffect } from 'react'
import { Bubble, Sender, XProvider } from '@ant-design/x'
import { UserOutlined, RobotOutlined, SendOutlined, ClearOutlined } from '@ant-design/icons'
import { Button, Space, Avatar } from 'antd'
import './ChatInterface.css'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  streaming?: boolean
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'assistant',
      content: '你好！我是AI助手，很高兴为您服务。请问有什么可以帮助您的吗？',
      timestamp: new Date(),
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const listRef = useRef<any>(null)

  // 自动滚动到底部
  useEffect(() => {
    if (listRef.current) {
      setTimeout(() => {
        listRef.current.scrollToBottom()
      }, 100)
    }
  }, [messages])

  // 发送消息
  const handleSend = async (message: string) => {
    if (!message.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: message.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    // 创建一个空的助手消息用于流式输出
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      streaming: true,
    }
    
    setMessages(prev => [...prev, assistantMessage])

    try {
      // 使用 SSE 连接后端
      const response = await fetch('http://localhost:8000/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message.trim() }),
      })

      if (!response.ok) {
        throw new Error('网络响应失败')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (reader) {
        let accumulatedContent = ''
        
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) break
          
          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') {
                break
              }
              
              try {
                const parsed = JSON.parse(data)
                if (parsed.content) {
                  accumulatedContent += parsed.content
                  
                  // 更新消息内容
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantMessageId
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  ))
                }
              } catch (e) {
                console.error('解析JSON失败:', e)
              }
            }
          }
        }
        
        // 流式传输完成，标记为非流式
        setMessages(prev => prev.map(msg => 
          msg.id === assistantMessageId
            ? { ...msg, streaming: false }
            : msg
        ))
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId
          ? { ...msg, content: '抱歉，发生了错误。请稍后再试。', streaming: false }
          : msg
      ))
    } finally {
      setLoading(false)
    }
  }

  // 清空对话
  const handleClear = () => {
    setMessages([{
      id: '0',
      role: 'assistant',
      content: '你好！我是AI助手，很高兴为您服务。请问有什么可以帮助您的吗？',
      timestamp: new Date(),
    }])
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
      <div className="chat-container">
        <div className="chat-header">
          <div className="chat-title">
            <RobotOutlined style={{ fontSize: 24, marginRight: 12 }} />
            <span>AI 助手</span>
          </div>
          <Button 
            icon={<ClearOutlined />} 
            onClick={handleClear}
            type="text"
            style={{ color: 'white' }}
          >
            清空对话
          </Button>
        </div>
        
        <div className="chat-body">
          <Bubble.List
            ref={listRef}
            items={bubbleItems as any}
            className="bubble-list"
          />
        </div>

        <div className="chat-footer">
          <Sender
            value={inputValue}
            onChange={setInputValue}
            onSubmit={handleSend}
            placeholder="输入消息..."
            loading={loading}
            allowSpeech={false}
            style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
            }}
          />
        </div>
      </div>
    </XProvider>
  )
}

export default ChatInterface

