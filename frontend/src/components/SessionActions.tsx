/**
 * 会话操作对话框组件
 * 包含重命名、删除确认、导出选项等对话框
 */
import { Modal, Input, Radio, message } from 'antd'
import { ExclamationCircleOutlined } from '@ant-design/icons'
import { useState } from 'react'
import type { ExportFormat } from '../api/client'

const { confirm } = Modal

interface RenameModalProps {
  visible: boolean
  currentTitle: string
  loading: boolean
  onOk: (newTitle: string) => void
  onCancel: () => void
}

/**
 * 重命名对话框
 */
export function RenameModal({
  visible,
  currentTitle,
  loading,
  onOk,
  onCancel,
}: RenameModalProps) {
  const [title, setTitle] = useState(currentTitle)

  const handleOk = () => {
    if (!title.trim()) {
      message.warning('标题不能为空')
      return
    }
    onOk(title.trim())
  }

  return (
    <Modal
      title="重命名会话"
      open={visible}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={loading}
      okText="确认"
      cancelText="取消"
      afterOpenChange={(open) => {
        if (open) {
          setTitle(currentTitle)
        }
      }}
    >
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="请输入新标题"
        maxLength={200}
        showCount
        autoFocus
        onPressEnter={handleOk}
      />
    </Modal>
  )
}

/**
 * 删除确认对话框
 */
export function showDeleteConfirm(
  sessionTitle: string,
  onConfirm: () => void
) {
  confirm({
    title: '确认删除会话',
    icon: <ExclamationCircleOutlined />,
    content: (
      <div>
        <p>确定要删除会话 <strong>"{sessionTitle}"</strong> 吗？</p>
        <p style={{ color: '#ff4d4f', marginTop: 8 }}>
          此操作将删除该会话及其所有消息，且不可恢复！
        </p>
      </div>
    ),
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: onConfirm,
  })
}

interface ExportModalProps {
  visible: boolean
  loading: boolean
  onOk: (format: ExportFormat) => void
  onCancel: () => void
}

/**
 * 导出选项对话框
 */
export function ExportModal({
  visible,
  loading,
  onOk,
  onCancel,
}: ExportModalProps) {
  const [format, setFormat] = useState<ExportFormat>('json')

  const handleOk = () => {
    onOk(format)
  }

  return (
    <Modal
      title="导出会话"
      open={visible}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={loading}
      okText="导出"
      cancelText="取消"
    >
      <div style={{ marginBottom: 16 }}>
        <p>请选择导出格式：</p>
      </div>
      <Radio.Group
        value={format}
        onChange={(e) => setFormat(e.target.value)}
        style={{ width: '100%' }}
      >
        <Radio value="json" style={{ display: 'block', marginBottom: 12 }}>
          <strong>JSON 格式</strong>
          <div style={{ color: '#666', fontSize: 12, marginTop: 4 }}>
            结构化数据，适合程序处理和备份
          </div>
        </Radio>
        <Radio value="markdown" style={{ display: 'block' }}>
          <strong>Markdown 格式</strong>
          <div style={{ color: '#666', fontSize: 12, marginTop: 4 }}>
            文本格式，适合阅读和分享
          </div>
        </Radio>
      </Radio.Group>
    </Modal>
  )
}

