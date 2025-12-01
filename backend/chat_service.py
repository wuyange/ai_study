"""
AutoGen 聊天服务
集成 AutoGen 框架实现与大模型的对话
支持多会话管理，每个会话使用独立的 agent
"""
import asyncio
import logging
from typing import AsyncGenerator, Optional, Any, Dict, List, TYPE_CHECKING
from collections import OrderedDict

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
    """聊天服务类，支持多会话管理
    
    特性：
    - 每个会话有独立的 agent 实例（保持独立的对话状态）
    - 使用 LRU 缓存限制 agent 数量，避免内存溢出
    - 自动清理不活跃的 agent
    """
    
    def __init__(self, settings: Settings, max_agents: int = 50):
        """初始化聊天服务
        
        Args:
            settings: 配置对象
            max_agents: 最大 agent 数量（LRU 缓存大小）
        """
        self.settings: Settings = settings
        self.model_client: Optional[OpenAIChatCompletionClient] = None
        self.initialized: bool = False
        
        # 多会话支持：session_id -> agent 映射
        self.agents: OrderedDict[str, AssistantAgent] = OrderedDict()
        self.max_agents: int = max_agents  # 最大 agent 数量
        
    async def initialize(self) -> None:
        """初始化 OpenAI 模型客户端（所有 agent 共享）"""
        if self.initialized:
            logger.warning("聊天服务已经初始化")
            return
        
        try:
            # 创建模型信息
            model_info = ModelInfo()
            
            # 创建模型客户端（所有 agent 共享同一个客户端）
            model_kwargs: Dict[str, Any] = {
                "model": self.settings.model_name,
                "api_key": self.settings.openai_api_key,
                "model_info": model_info.model_dump(),
            }
            
            if self.settings.openai_api_base:
                model_kwargs["base_url"] = self.settings.openai_api_base
            
            logger.info(f"正在创建模型客户端: {self.settings.model_name}")
            self.model_client = OpenAIChatCompletionClient(**model_kwargs)
            
            self.initialized = True
            logger.info(f"✓ 聊天服务初始化完成 (模型: {self.settings.model_name})")
            
        except Exception as e:
            logger.error(f"初始化失败: {str(e)}", exc_info=True)
            raise
    
    def _get_or_create_agent(self, session_id: str) -> AssistantAgent:
        """获取或创建会话的 agent
        
        每个会话有独立的 agent 实例，使用 LRU 缓存策略。
        
        Args:
            session_id: 会话 ID
            
        Returns:
            该会话的 agent 实例
        """
        if not self.initialized or not self.model_client:
            raise RuntimeError("聊天服务未初始化")
        
        # 如果 agent 已存在，移到最后（LRU）
        if session_id in self.agents:
            self.agents.move_to_end(session_id)
            logger.debug(f"使用已存在的 agent (会话: {session_id[:8]}...)")
            return self.agents[session_id]
        
        # 创建新的 agent
        logger.info(f"为会话创建新 agent (会话: {session_id[:8]}...)")
        agent = AssistantAgent(
            name=f"assistant_{session_id[:8]}",
            model_client=self.model_client,
            system_message=self.settings.system_message,
            model_client_stream=True
        )
        
        self.agents[session_id] = agent
        
        # LRU 缓存：如果超过最大数量，删除最旧的
        if len(self.agents) > self.max_agents:
            oldest_session_id = next(iter(self.agents))
            removed_agent = self.agents.pop(oldest_session_id)
            logger.info(f"删除最旧的 agent (会话: {oldest_session_id[:8]}..., 当前 agent 数: {len(self.agents)})")
        
        logger.debug(f"当前活跃 agent 数量: {len(self.agents)}")
        return agent
    
    def remove_agent(self, session_id: str) -> None:
        """移除会话的 agent（当会话被删除时调用）
        
        Args:
            session_id: 会话 ID
        """
        if session_id in self.agents:
            self.agents.pop(session_id)
            logger.info(f"删除 agent (会话: {session_id[:8]}..., 剩余 agent: {len(self.agents)})")
    
    def clear_all_agents(self) -> None:
        """清除所有 agent（用于重置）"""
        count = len(self.agents)
        self.agents.clear()
        logger.info(f"清除了 {count} 个 agent")
    
    def _extract_response(self, response: Any) -> str:
        """提取响应内容"""
        if hasattr(response, 'messages') and response.messages:
            last_message = response.messages[-1]
            if hasattr(last_message, 'content'):
                return str(last_message.content)
            return str(last_message)
        
        return str(response)
    
    async def chat(self, message: str) -> str:
        """非流式聊天（兼容旧接口，使用临时 agent）"""
        if not self.initialized or not self.model_client:
            raise RuntimeError("聊天服务未初始化")
        
        try:
            logger.debug(f"处理聊天请求: {message}")
            
            # 使用临时 agent
            temp_agent = AssistantAgent(
                name="assistant_temp",
                model_client=self.model_client,
                system_message=self.settings.system_message,
            )
            
            # 运行代理
            response = await temp_agent.run(task=message)
            
            # 提取响应内容
            result = self._extract_response(response)
            logger.debug(f"聊天响应: {result[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"聊天错误: {str(e)}", exc_info=True)
            raise
    
    async def stream_chat(self, message: str) -> AsyncGenerator[str, None]:
        """流式聊天（兼容旧接口，使用临时 agent）"""
        if not self.initialized or not self.model_client:
            raise RuntimeError("聊天服务未初始化")
        
        try:
            logger.debug(f"处理流式聊天请求: {message}")
            
            # 使用临时 agent
            temp_agent = AssistantAgent(
                name="assistant",
                model_client=self.model_client,
                system_message=self.settings.system_message,
                model_client_stream=True
            )
            
            # 使用 AutoGen 的流式 API
            response = temp_agent.run_stream(task=message)

            async for chunk in response:
                if isinstance(chunk, ModelClientStreamingChunkEvent) and chunk.source == "assistant":
                    yield chunk.content
                
        except Exception as e:
            error_msg = f"流式聊天错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"抱歉，发生了错误: {str(e)}"
    
    async def chat_with_context(
        self, 
        session_id: str,
        message: str, 
        history: List["Message"]
    ) -> str:
        """带上下文的聊天（多会话版本）
        
        将历史消息作为上下文传递给 AI，实现多轮对话。
        每个会话使用独立的 agent。
        
        Args:
            session_id: 会话 ID
            message: 用户当前消息
            history: 历史消息列表（已按时间排序）
            
        Returns:
            AI 的回复内容
        """
        if not self.initialized:
            raise RuntimeError("聊天服务未初始化")
        
        try:
            # 获取或创建该会话的 agent
            agent = self._get_or_create_agent(session_id)
            
            logger.debug(f"处理带上下文的聊天请求 (会话: {session_id[:8]}...): {message[:50]}...")
            logger.debug(f"上下文包含 {len(history)} 条历史消息")
            
            # 构建完整的对话上下文
            # 如果有历史消息，将其作为系统上下文
            if history:
                context_messages = []
                for msg in history:
                    context_messages.append(f"{msg.role}: {msg.content}")
                
                # 构建包含历史的完整提示
                full_prompt = f"以下是之前的对话历史：\n\n" + "\n\n".join(context_messages)
                full_prompt += f"\n\n现在用户说：{message}\n\n请基于上下文回复用户。"
                
                response = await agent.run(task=full_prompt)
            else:
                # 没有历史记录，直接回答
                response = await agent.run(task=message)
            
            result = self._extract_response(response)
            logger.debug(f"聊天响应: {result[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"带上下文聊天错误: {str(e)}", exc_info=True)
            raise
    
    async def stream_chat_with_context(
        self,
        session_id: str,
        message: str,
        history: List["Message"]
    ) -> AsyncGenerator[str, None]:
        """带上下文的流式聊天（多会话版本）
        
        每个会话使用独立的 agent。
        
        Args:
            session_id: 会话 ID
            message: 用户当前消息
            history: 历史消息列表
            
        Yields:
            AI 回复的文本片段
        """
        if not self.initialized:
            raise RuntimeError("聊天服务未初始化")
        
        try:
            # 获取或创建该会话的 agent
            agent = self._get_or_create_agent(session_id)
            
            logger.debug(f"处理带上下文的流式聊天 (会话: {session_id[:8]}...): {message[:50]}...")
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
            response = agent.run_stream(task=full_prompt)
            
            chunk_count = 0
            async for chunk in response:
                if isinstance(chunk, ModelClientStreamingChunkEvent) and chunk.source.startswith("assistant"):
                    chunk_count += 1
                    yield chunk.content
            
            logger.info(f"流式聊天完成 (会话: {session_id[:8]}...)，共生成 {chunk_count} 个内容块")
            
        except Exception as e:
            error_msg = f"带上下文流式聊天错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"抱歉，发生了错误: {str(e)}"
    
    async def generate_title(self, first_message: str) -> str:
        """根据首条消息生成会话标题
        
        使用 AI 生成一个简短、概括性的标题（10-20字）。
        使用临时 agent，不影响会话状态。
        
        Args:
            first_message: 会话的第一条用户消息
            
        Returns:
            生成的标题
        """
        if not self.initialized or not self.model_client:
            raise RuntimeError("聊天服务未初始化")
        
        try:
            logger.debug(f"为消息生成标题: {first_message[:50]}...")
            
            # 使用临时 agent 生成标题
            temp_agent = AssistantAgent(
                name="title_generator",
                model_client=self.model_client,
                system_message="你是一个标题生成助手，专门为对话生成简短准确的标题。",
            )
            
            prompt = f"""请为以下用户消息生成一个简短的对话标题。

                    要求：
                    1. 长度：10-20个汉字
                    2. 准确概括对话主题
                    3. 只返回标题文本，不要其他内容
                    4. 不要使用引号或标点符号
                    
                    用户消息：
                    {first_message}
                    
                    标题："""
            
            response = await temp_agent.run(task=prompt)
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
            self.clear_all_agents()
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
