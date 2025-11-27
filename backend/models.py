"""
数据模型定义
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


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

