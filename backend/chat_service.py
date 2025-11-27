"""
AutoGen 聊天服务
集成 AutoGen 框架实现与大模型的对话
"""
import asyncio
import logging
from typing import AsyncGenerator, Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务类"""
    
    def __init__(self, settings):
        self.settings = settings
        self.agent: Optional[AssistantAgent] = None
        self.model_client: Optional[OpenAIChatCompletionClient] = None
        self.initialized = False
        
    async def initialize(self):
        """初始化 AutoGen 代理"""
        if self.initialized:
            logger.warning("聊天服务已经初始化")
            return
        
        try:
            # 创建模型客户端
            model_kwargs = {
                "model": self.settings.model_name,
                "api_key": self.settings.openai_api_key,
                "model_info":{
                    "family": ModelFamily.UNKNOWN,
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "structured_output": True,
                    "multiple_system_messages": True,
                }
            }
            
            if self.settings.openai_api_base:
                model_kwargs["base_url"] = self.settings.openai_api_base
            
            logger.info(f"正在创建模型客户端: {self.settings.model_name}")
            self.model_client = OpenAIChatCompletionClient(**model_kwargs)
            
            # 创建助手代理
            logger.info("正在创建助手代理...")
            self.agent = AssistantAgent(
                name="assistant",
                model_client=self.model_client,
                system_message=self.settings.system_message
            )
            
            self.initialized = True
            logger.info(f"✓ AutoGen 代理初始化完成 (模型: {self.settings.model_name})")
            
        except Exception as e:
            logger.error(f"初始化失败: {str(e)}", exc_info=True)
            raise
    
    async def chat(self, message: str) -> str:
        """非流式聊天"""
        if not self.initialized or not self.agent:
            raise RuntimeError("聊天服务未初始化")
        
        try:
            logger.debug(f"处理聊天请求: {message}")
            
            # 运行代理
            response = await self.agent.run(task=message)
            
            # 提取响应内容
            result = self._extract_response(response)
            logger.debug(f"聊天响应: {result[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"聊天错误: {str(e)}", exc_info=True)
            raise
    
    def _extract_response(self, response) -> str:
        """提取响应内容"""
        if hasattr(response, 'messages') and response.messages:
            last_message = response.messages[-1]
            if hasattr(last_message, 'content'):
                return last_message.content
            return str(last_message)
        
        return str(response)
    
    async def stream_chat(self, message: str) -> AsyncGenerator[str, None]:
        """流式聊天"""
        if not self.initialized or not self.agent:
            raise RuntimeError("聊天服务未初始化")
        
        try:
            logger.debug(f"处理流式聊天请求: {message}")
            
            # 使用 AutoGen 的流式 API
            response = await self.agent.run(task=message)
            
            # 提取完整响应
            full_response = self._extract_response(response)
            logger.debug(f"流式聊天完整响应: {full_response[:100]}...")
            
            # 模拟流式输出（逐字输出）
            # 注意：AutoGen AgentChat 当前版本可能不直接支持流式输出
            # 这里我们将完整响应分块发送以模拟流式效果
            chunk_size = self.settings.stream_chunk_size
            
            # 按字分割（适合中文）
            chars = list(full_response)
            for i in range(0, len(chars), chunk_size):
                chunk = ''.join(chars[i:i + chunk_size])
                yield chunk
                await asyncio.sleep(self.settings.stream_delay)
                
        except Exception as e:
            error_msg = f"流式聊天错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"抱歉，发生了错误: {str(e)}"
    
    async def cleanup(self):
        """清理资源"""
        try:
            self.agent = None
            self.model_client = None
            self.initialized = False
            logger.info("✓ 聊天服务资源已清理")
        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}", exc_info=True)


# 用于测试的主函数
async def main():
    """测试函数"""
    from config import get_settings
    
    settings = get_settings()
    service = ChatService(settings)
    
    try:
        await service.initialize()
        
        # 测试非流式聊天
        print("\n=== 测试非流式聊天 ===")
        response = await service.chat("你好，请介绍一下你自己")
        print(f"响应: {response}")
        
        # 测试流式聊天
        print("\n=== 测试流式聊天 ===")
        print("响应: ", end="", flush=True)
        async for chunk in service.stream_chat("用一句话解释什么是人工智能"):
            print(chunk, end="", flush=True)
        print()
        
    finally:
        await service.cleanup()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

