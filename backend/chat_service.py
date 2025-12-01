"""
AutoGen 聊天服务
集成 AutoGen 框架实现与大模型的对话
"""
import asyncio
import logging
from typing import AsyncGenerator, Optional, Any, Dict, List, TYPE_CHECKING

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage, BaseAgentEvent, BaseChatMessage, ModelClientStreamingChunkEvent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from config import Settings
from models import ModelInfo

if TYPE_CHECKING:
    from database import Message

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
                system_message=self.settings.system_message,
                model_client_stream=True
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

    
    async def stream_chat(self, message: str) -> AsyncGenerator[str, None]:
        """流式聊天"""
        if not self.initialized or not self.agent:
            raise RuntimeError("聊天服务未初始化")
        
        try:
            logger.debug(f"处理流式聊天请求: {message}")
            
            # 使用 AutoGen 的流式 API
            response = self.agent.run_stream(task=message)

            async for chunk in response:
                if isinstance(chunk, ModelClientStreamingChunkEvent) and chunk.source == "assistant":
                    yield chunk.content
                
        except Exception as e:
            error_msg = f"流式聊天错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"抱歉，发生了错误: {str(e)}"
    
    async def chat_with_context(
        self, 
        message: str, 
        history: List["Message"]
    ) -> str:
        """带上下文的聊天
        
        将历史消息作为上下文传递给 AI，实现多轮对话。
        
        Args:
            message: 用户当前消息
            history: 历史消息列表（已按时间排序）
            
        Returns:
            AI 的回复内容
        """
        if not self.initialized or not self.agent:
            raise RuntimeError("聊天服务未初始化")
        
        try:
            logger.debug(f"处理带上下文的聊天请求: {message[:50]}...")
            logger.debug(f"上下文包含 {len(history)} 条历史消息")
            
            # 构建完整的对话上下文
            # AutoGen 的 run 方法会自动管理对话历史
            # 我们需要将历史消息转换为合适的格式
            
            # 如果有历史消息，将其作为系统上下文
            if history:
                context_messages = []
                for msg in history:
                    context_messages.append(f"{msg.role}: {msg.content}")
                
                # 构建包含历史的完整提示
                full_prompt = f"以下是之前的对话历史：\n\n" + "\n\n".join(context_messages)
                full_prompt += f"\n\n现在用户说：{message}\n\n请基于上下文回复用户。"
                
                response = await self.agent.run(task=full_prompt)
            else:
                # 没有历史记录，直接回答
                response = await self.agent.run(task=message)
            
            result = self._extract_response(response)
            logger.debug(f"聊天响应: {result[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"带上下文聊天错误: {str(e)}", exc_info=True)
            raise
    
    async def stream_chat_with_context(
        self,
        message: str,
        history: List["Message"]
    ) -> AsyncGenerator[str, None]:
        """带上下文的流式聊天
        
        Args:
            message: 用户当前消息
            history: 历史消息列表
            
        Yields:
            AI 回复的文本片段
        """
        if not self.initialized or not self.agent:
            raise RuntimeError("聊天服务未初始化")
        
        try:
            logger.debug(f"处理带上下文的流式聊天: {message[:50]}...")
            logger.debug(f"上下文包含 {len(history)} 条历史消息")
            
            # 构建完整对话上下文
            if history:
                context_messages = []
                for msg in history:
                    context_messages.append(f"{msg.role}: {msg.content}")
                
                full_prompt = f"以下是之前的对话历史：\n\n" + "\n\n".join(context_messages)
                full_prompt += f"\n\n现在用户说：{message}\n\n请基于上下文回复用户。"
            else:
                full_prompt = message
            
            # 调用流式 API
            response = self.agent.run_stream(task=full_prompt)
            
            chunk_count = 0
            async for chunk in response:
                if isinstance(chunk, ModelClientStreamingChunkEvent) and chunk.source == "assistant":
                    chunk_count += 1
                    yield chunk.content
            
            logger.info(f"流式聊天完成，共生成 {chunk_count} 个内容块")
            
        except Exception as e:
            error_msg = f"带上下文流式聊天错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"抱歉，发生了错误: {str(e)}"
    
    async def generate_title(self, first_message: str) -> str:
        """根据首条消息生成会话标题
        
        使用 AI 生成一个简短、概括性的标题（10-20字）。
        
        Args:
            first_message: 会话的第一条用户消息
            
        Returns:
            生成的标题
        """
        if not self.initialized or not self.agent:
            raise RuntimeError("聊天服务未初始化")
        
        try:
            logger.debug(f"为消息生成标题: {first_message[:50]}...")
            
            prompt = f"""请为以下用户消息生成一个简短的对话标题。

要求：
1. 长度：10-20个汉字
2. 准确概括对话主题
3. 只返回标题文本，不要其他内容
4. 不要使用引号或标点符号

用户消息：
{first_message}

标题："""
            
            response = await self.agent.run(task=prompt)
            title = self._extract_response(response).strip()
            
            # 清理标题（移除引号、换行等）
            title = title.replace('"', '').replace("'", '').replace('\n', ' ').strip()
            
            # 限制长度
            if len(title) > 30:
                title = title[:30] + "..."
            
            # 如果标题为空，使用默认值
            if not title:
                title = "新对话"
            
            logger.info(f"生成的标题: {title}")
            return title
            
        except Exception as e:
            logger.error(f"标题生成失败: {str(e)}", exc_info=True)
            # 降级方案：使用首条消息的前20个字符
            return first_message[:20] + "..." if len(first_message) > 20 else first_message
    
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

