import { useState, useRef, useEffect } from 'react'
import { ConfigProvider, theme } from 'antd'
import ChatInterface from './components/ChatInterface'
import './App.css'

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#667eea',
          borderRadius: 16,
          colorBgContainer: '#ffffff',
          colorText: '#1a1a1a',
        },
      }}
    >
      <div className="app-container">
        <ChatInterface />
      </div>
    </ConfigProvider>
  )
}

export default App

