# -*- coding: utf-8 -*-
"""
Custom DeepSeek Reasoner ChatModel for LangChain 1.0.
"""

import os
import json
from typing import Any, List, Optional, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.tools import BaseTool
from pydantic import Field

# 尝试导入 OpenAI 客户端
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# DeepSeek Reasoner 模型封装
class DeepSeekReasonerChatModel(BaseChatModel):
    """
    DeepSeek Reasoner model wrapper that preserves reasoning_content.
    """

    api_key: str = Field(default=None)
    base_url: str = Field(default="https://api.deepseek.com")
    model_name: str = Field(default="deepseek-reasoner")
    temperature: float = Field(default=0.7)
    timeout: float = Field(default=60.0)
    bound_tools: Optional[List[Dict]] = Field(default=None)

    _client: Optional[Any] = None

    # 初始化模型客户端与鉴权信息
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if OpenAI is None:
            raise ImportError("openai library is required. Install with: pip install openai")

        if not self.api_key:
            self.api_key = os.environ.get("DEEPSEEK_API_KEY")

        if not self.api_key:
            raise ValueError("api_key must be provided or DEEPSEEK_API_KEY must be set")

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

    @property
    # 返回模型类型标识
    def _llm_type(self) -> str:
        return "deepseek_reasoner"

    @property
    # 返回模型标识参数
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "temperature": self.temperature,
        }

    # 将 LangChain 消息转换为 OpenAI 兼容格式
    def _convert_messages_to_openai_format(
        self, messages: List[BaseMessage]
    ) -> List[Dict]:
        openai_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                openai_messages.append({
                    "role": "user",
                    "content": msg.content
                })

            elif isinstance(msg, SystemMessage):
                openai_messages.append({
                    "role": "system",
                    "content": msg.content
                })

            elif isinstance(msg, AIMessage):
                msg_dict = {
                    "role": "assistant",
                    "content": msg.content or "",
                }

                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls = []
                    for tc in msg.tool_calls:
                        tool_calls.append({
                            "id": tc.get("id") if isinstance(tc, dict) else tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.get("name") if isinstance(tc, dict) else tc.name,
                                "arguments": json.dumps(
                                    tc.get("args") if isinstance(tc, dict) else tc.args
                                )
                            }
                        })
                    msg_dict["tool_calls"] = tool_calls

                if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
                    if "reasoning_content" in msg.additional_kwargs:
                        msg_dict["reasoning_content"] = msg.additional_kwargs["reasoning_content"]

                openai_messages.append(msg_dict)

            elif isinstance(msg, ToolMessage):
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "name": msg.name if hasattr(msg, "name") else "",
                    "content": msg.content
                })

        return openai_messages

    # 将 OpenAI 响应转换为 AIMessage
    def _create_ai_message_from_response(self, response) -> AIMessage:
        message = response.choices[0].message

        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append({
                    "name": tc.function.name,
                    "args": json.loads(tc.function.arguments),
                    "id": tc.id,
                })

        additional_kwargs = {}
        if hasattr(message, "reasoning_content") and message.reasoning_content:
            additional_kwargs["reasoning_content"] = message.reasoning_content

        ai_message_kwargs = {
            "content": message.content or "",
            "additional_kwargs": additional_kwargs
        }

        if tool_calls:
            ai_message_kwargs["tool_calls"] = tool_calls

        return AIMessage(**ai_message_kwargs)

    # 生成回复的核心方法
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # 消息格式转换
        openai_messages = self._convert_messages_to_openai_format(messages)

        # 组装请求参数
        request_params = {
            "model": self.model_name,
            "messages": openai_messages,
            "temperature": self.temperature,
        }

        # 附加工具定义（如已绑定）
        if self.bound_tools:
            request_params["tools"] = self.bound_tools

        # 附加停止词
        if stop:
            request_params["stop"] = stop

        # 调用模型接口
        response = self._client.chat.completions.create(**request_params)

        # 构造 AIMessage
        ai_message = self._create_ai_message_from_response(response)

        # 返回标准化结果
        generation = ChatGeneration(message=ai_message)
        return ChatResult(generations=[generation])

    # 绑定工具为 OpenAI 工具定义并返回新实例
    def bind_tools(
        self,
        tools: List[BaseTool],
        **kwargs: Any
    ) -> "DeepSeekReasonerChatModel":
        # 转换工具定义
        openai_tools = []
        for tool in tools:
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                }
            }

            # 附加参数 schema
            if hasattr(tool, "args_schema") and tool.args_schema:
                tool_def["function"]["parameters"] = tool.args_schema.model_json_schema()
            else:
                tool_def["function"]["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }

            openai_tools.append(tool_def)

        # 返回绑定后的新模型实例
        return self.__class__(
            api_key=self.api_key,
            base_url=self.base_url,
            model_name=self.model_name,
            temperature=self.temperature,
            timeout=self.timeout,
            bound_tools=openai_tools,
            **kwargs
        )


__all__ = ["DeepSeekReasonerChatModel"]
