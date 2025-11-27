"""
数据模型定义
"""
from typing import Optional, Literal
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

