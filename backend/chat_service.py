"""
AutoGen 聊天服务
集成 AutoGen 框架实现与大模型的对话
"""
import asyncio
import logging
from typing import AsyncGenerator, Optional, Any, Dict

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage, BaseAgentEvent, BaseChatMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from config import Settings
from models import ModelInfo

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务类"""
    
    def __init__(self, settings: Settings) -> None:
        self.settings: Settings = settings
        self.agent: Optional[AssistantAgent] = None
        self.model_client: Optional[OpenAIChatCompletionClient] = None
        self.initialized: bool = False
        
    async def initialize(self) -> None:
        """初始化 AutoGen 代理"""
        if self.initialized:
            logger.warning("聊天服务已经初始化")
            return
        
        try:
            # 创建模型信息
            model_info = ModelInfo()
            
            # 创建模型客户端
            model_kwargs: Dict[str, Any] = {
                "model": self.settings.model_name,
                "api_key": self.settings.openai_api_key,
                "model_info": model_info.model_dump(),
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
    
    def _extract_response(self, response: Any) -> str:
        """提取响应内容"""
        if hasattr(response, 'messages') and response.messages:
            last_message = response.messages[-1]
            if hasattr(last_message, 'content'):
                return str(last_message.content)
            return str(last_message)
        
        return str(response)

    def _is_message_event(self, event: Any) -> bool:
        """判断事件是否为消息类型
        
        Args:
            event: AutoGen 事件对象
            
        Returns:
            True 如果是消息事件，False 否则
        """
        return isinstance(event, (TaskResult, BaseChatMessage))
    
    def _extract_content_from_event(self, event: Any) -> Optional[str]:
        """从事件中提取文本内容
        
        Args:
            event: AutoGen 事件对象
            
        Returns:
            提取的文本内容，如果无法提取则返回 None
        """
        if isinstance(event, TaskResult):
            return self._extract_response(event)
        elif isinstance(event, BaseChatMessage):
            # 只处理助手的消息
            if hasattr(event, 'source') and event.source == "assistant":
                return str(event.content) if event.content else None
            # 如果没有 source 属性，也返回内容
            return str(event.content) if event.content else None
        return None
    
    async def stream_chat(self, message: str) -> AsyncGenerator[str, None]:
        """流式聊天
        
        使用 AutoGen 的 run_stream API 实现真正的流式输出。
        逐步返回 AI 的回复内容，适用于实时对话场景。
        
        Args:
            message: 用户输入的消息
            
        Yields:
            str: AI 回复的文本片段
            
        Raises:
            RuntimeError: 当聊天服务未初始化时抛出
        """
        # 1. 验证服务状态
        if not self.initialized or not self.agent:
            error_msg = "聊天服务未初始化"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.debug(f"开始处理流式聊天请求: {message[:50]}...")
        
        try:
            # 2. 调用 AutoGen 流式 API
            event_stream = self.agent.run_stream(task=message)
            
            # 3. 处理事件流
            chunk_count = 0
            async for event in event_stream:
                # 跳过非消息事件
                if not self._is_message_event(event):
                    logger.debug(f"跳过非消息事件: {type(event).__name__}")
                    continue
                
                # 提取内容
                content = self._extract_content_from_event(event)
                if content:
                    chunk_count += 1
                    logger.debug(f"生成内容块 #{chunk_count}: {content[:30]}...")
                    yield content
                    
                    # 可选：添加延迟以控制输出速度
                    if self.settings.stream_delay > 0:
                        await asyncio.sleep(self.settings.stream_delay)
            
            logger.info(f"流式聊天完成，共生成 {chunk_count} 个内容块")
            
        except Exception as e:
            error_msg = f"流式聊天处理失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # 返回友好的错误消息
            yield f"抱歉，处理您的请求时发生了错误。请稍后重试。"
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            self.agent = None
            self.model_client = None
            self.initialized = False
            logger.info("✓ 聊天服务资源已清理")
        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}", exc_info=True)


# 用于测试的主函数
async def main() -> None:
    """测试函数"""
    from config import get_settings
    
    settings: Settings = get_settings()
    service: ChatService = ChatService(settings)
    
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

