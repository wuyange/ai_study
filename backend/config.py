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

    quality_message: str = Field(
        default="""
# Role
你是一个严格的AI回答质量质检员。你的任务是根据特定维度评估给定的回答，并给出明确的判定结论及理由。

# Evaluation Criteria (评分维度)
请基于以下三个维度对输入内容进行逻辑判断：
1. **准确性**：内容是否客观、事实准确，无误导性信息？
2. **理解难度**：逻辑是否清晰，表达是否通俗易懂，符合用户认知水平？
3. **语言精炼**：是否在不丢失信息的前提下做到了简洁，无冗余废话？

# Decision Logic (判定逻辑)
- 如果上述三个维度 **全部** 达标，判定结果为：`pass`
- 如果上述任意一个维度 **不** 达标，判定结果为：`notApproved`

# Output Constraints (输出强制约束)
1. **重要**：在输出任何文字之前，必须先输出一个换行符（空一行）。
2. 请严格按照以下格式输出，不要包含其他多余的引导语：

Status: [这里只填写 "pass" 或 "notApproved"]
Reason: [这里填写具体的评价理由]
        """,
        env="QUALITY_MESSAGE"
    )
    
    # 流式输出配置
    stream_chunk_size: int = Field(default=1, env="STREAM_CHUNK_SIZE")
    stream_delay: float = Field(default=0.05, env="STREAM_DELAY")
    
    # 日志配置 (loguru)
    log_dir: str = Field(default="logs", env="LOG_DIR")
    log_level: str = Field(default="DEBUG", env="LOG_LEVEL")
    log_rotation: str = Field(default="10 MB", env="LOG_ROTATION")  # 日志轮转大小
    log_retention: str = Field(default="7 days", env="LOG_RETENTION")  # 日志保留时间
    
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

