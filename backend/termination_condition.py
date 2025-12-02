from typing import Sequence

from autogen_agentchat.base import TerminatedException, TerminationCondition
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage, StopMessage
from autogen_core import Component
from pydantic import BaseModel
from typing_extensions import Self


# 1. 定义配置类 (用于序列化)
class SourcePrefixTerminationConfig(BaseModel):
    """Configuration for the prefix match termination condition."""
    prefix: str


# 2. 定义主逻辑类
class SourcePrefixTermination(TerminationCondition, Component[SourcePrefixTerminationConfig]):
    """Terminate the conversation if a message is received from a source starting with a specific prefix."""

    # 指定配置模式
    component_config_schema = SourcePrefixTerminationConfig
    # 如果你是作为库发布，这里写完整的包路径；如果是本地运行，保持默认或自定义字符串
    component_provider_override = "backend.termination_condition.SourcePrefixTermination"

    def __init__(self, prefix: str) -> None:
        self._terminated = False
        self._prefix = prefix

    @property
    def terminated(self) -> bool:
        return self._terminated

    async def __call__(self, messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> StopMessage | None:
        # 如果已经终止，防止重复调用
        if self._terminated:
            raise TerminatedException("Termination condition has already been reached")

        # 遍历当前批次的消息
        for message in messages:
            # 检查消息是否有 source 属性，并且是否以指定前缀开头
            if hasattr(message, "source") and message.source.startswith(self._prefix):
                self._terminated = True
                return StopMessage(
                    content=f"Terminated because source '{message.source}' starts with '{self._prefix}'.",
                    source="SourcePrefixTermination",
                )
        return None

    async def reset(self) -> None:
        self._terminated = False

    def _to_config(self) -> SourcePrefixTerminationConfig:
        return SourcePrefixTerminationConfig(
            prefix=self._prefix,
        )

    @classmethod
    def _from_config(cls, config: SourcePrefixTerminationConfig) -> Self:
        return cls(
            prefix=config.prefix,
        )