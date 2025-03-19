from autogen_core.tool_agent import ToolAgent, tool_agent_caller_loop
from autogen_core.tools import FunctionTool, Tool, ToolSchema
from dataclasses import dataclass

from typing import List
from pydantic import BaseModel
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.models.azure import AzureAIChatCompletionClient

from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    LLMMessage,
    SystemMessage,
    UserMessage,
    FunctionExecutionResult
)
from autogen_core import RoutedAgent, message_handler
from autogen_core import AgentId, MessageContext
from autogen_core import (
    DefaultTopicId,
    RoutedAgent,
    default_subscription,
    message_handler,
    type_subscription,
    Image
)
from typing import Optional
from autogen_core import SingleThreadedAgentRuntime

import asyncio