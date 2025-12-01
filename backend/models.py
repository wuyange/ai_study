"""
数据模型定义
"""
from datetime import datetime
from typing import Optional, Literal, List
from enum import Enum
from pydantic import BaseModel, Field
from autogen_core.models import ModelFamily


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "你好，请介绍一下你自己"
            }
        }


class ChatResponse(BaseModel):
    """聊天响应模型"""
    content: str = Field(..., description="AI 回复内容")
    role: Literal["assistant"] = Field(default="assistant", description="角色")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "你好！我是 AI 助手，很高兴为您服务。",
                "role": "assistant"
            }
        }


class StreamChunk(BaseModel):
    """流式输出数据块"""
    content: str = Field(..., description="内容片段")
    role: Literal["assistant"] = Field(default="assistant", description="角色")
    done: bool = Field(default=False, description="是否完成")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "服务器错误",
                "detail": "无法连接到 OpenAI API"
            }
        }


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: Literal["healthy", "unhealthy"] = Field(..., description="服务状态")
    service: str = Field(default="chat-api", description="服务名称")
    autogen_initialized: bool = Field(..., description="AutoGen 是否已初始化")
    version: str = Field(default="1.0.0", description="API 版本")


class ModelInfo(BaseModel):
    """模型信息配置"""
    family: ModelFamily = Field(default=ModelFamily.UNKNOWN, description="模型家族")
    vision: bool = Field(default=False, description="是否支持视觉")
    function_calling: bool = Field(default=True, description="是否支持函数调用")
    json_output: bool = Field(default=True, description="是否支持 JSON 输出")
    structured_output: bool = Field(default=True, description="是否支持结构化输出")
    multiple_system_messages: bool = Field(default=True, description="是否支持多条系统消息")
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "family": "UNKNOWN",
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": True,
                "multiple_system_messages": True
            }
        }
    }


# ============= 会话管理相关模型 =============

class ExportFormat(str, Enum):
    """导出格式枚举"""
    JSON = "json"
    MARKDOWN = "markdown"


class SessionCreate(BaseModel):
    """创建会话请求"""
    title: Optional[str] = Field(default="新对话", description="会话标题")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "讨论 Python 编程"
            }
        }
    }


class SessionResponse(BaseModel):
    """会话响应"""
    id: str = Field(..., description="会话 ID")
    title: str = Field(..., description="会话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    message_count: Optional[int] = Field(default=0, description="消息数量")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "讨论 Python 编程",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:30:00",
                "message_count": 10
            }
        }
    }


class SessionList(BaseModel):
    """会话列表响应"""
    sessions: List[SessionResponse] = Field(..., description="会话列表")
    total: int = Field(..., description="总数")


class MessageResponse(BaseModel):
    """消息响应"""
    id: str = Field(..., description="消息 ID")
    session_id: str = Field(..., description="会话 ID")
    role: Literal["user", "assistant"] = Field(..., description="角色")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(..., description="时间戳")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "msg-001",
                "session_id": "session-001",
                "role": "user",
                "content": "你好",
                "timestamp": "2024-01-01T12:00:00"
            }
        }
    }


class ChatRequestWithSession(BaseModel):
    """带会话 ID 的聊天请求"""
    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")
    session_id: str = Field(..., description="会话 ID")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "什么是人工智能？",
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    }


class UpdateSessionTitle(BaseModel):
    """更新会话标题请求"""
    title: str = Field(..., min_length=1, max_length=200, description="新标题")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "AI 基础知识讨论"
            }
        }
    }


class ExportRequest(BaseModel):
    """导出请求"""
    format: ExportFormat = Field(default=ExportFormat.JSON, description="导出格式")


class ExportResponse(BaseModel):
    """导出响应"""
    content: str = Field(..., description="导出的内容")
    format: ExportFormat = Field(..., description="导出格式")
    filename: str = Field(..., description="建议的文件名")

