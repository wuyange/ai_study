"""
配置管理模块
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # OpenAI 配置
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_api_base: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        env="OPENAI_API_BASE"
    )
    model_name: str = Field(default="qwen3-max", env="MODEL_NAME")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # CORS 配置
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        env="CORS_ORIGINS"
    )
    
    # Agent 配置
    system_message: str = Field(
        default="你是一个友好、专业的AI助手。请用简洁、准确的中文回答用户的问题。",
        env="SYSTEM_MESSAGE"
    )
    
    # 流式输出配置
    stream_chunk_size: int = Field(default=1, env="STREAM_CHUNK_SIZE")
    stream_delay: float = Field(default=0.05, env="STREAM_DELAY")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """将 CORS 源字符串转换为列表"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 创建全局配置实例
def get_settings() -> Settings:
    """获取配置实例"""
    return Settings()

