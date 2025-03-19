from dataclasses import dataclass
import time
from typing import List
from pydantic import BaseModel
from autogen_core.components.models import (
    AssistantMessage,
    ChatCompletionClient,
    AzureOpenAIChatCompletionClient,
    LLMMessage,
    SystemMessage,
    UserMessage,
    FunctionExecutionResult
)
from autogen_core.components import RoutedAgent, message_handler
from autogen_core.base import AgentId, MessageContext
from autogen_core.components import (
    DefaultTopicId,
    RoutedAgent,
    default_subscription,
    message_handler,
    type_subscription,
    Image
)

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import asyncio
import uuid
from dotenv import load_dotenv
import os


token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

load_dotenv()

endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
deployed_model = os.environ["DEPLOYMENT_NAME"]

def get_model_client() -> AzureOpenAIChatCompletionClient:
    return AzureOpenAIChatCompletionClient(
    model=deployed_model,
    api_version="2024-02-01",
    azure_endpoint=endpoint,
    azure_ad_token_provider=token_provider,
    model_capabilities={
            "vision":True,
            "function_calling":True,
            "json_output":True,
            "streaming":True,
            "max_tokens":1000,
            "temperature":0.0
        }
    )


class Message(BaseModel):
    body: LLMMessage

class StreamResponse(BaseModel):
    body: LLMMessage

class GroupChatMessage(BaseModel):
    body: LLMMessage
    conversation_id: str 

class ToolResult(BaseModel):
    body: List[LLMMessage]
    conversation_id: str 

class ToolAgentMessage(BaseModel):
    body: LLMMessage
    conversation_id: str 

class FinalResult(BaseModel):
    body: LLMMessage


class IntermediateResult(BaseModel):
    body: List[LLMMessage]
    conversation_id: str 

class ImageAnalysisMessage(BaseModel):
    body: LLMMessage
    conversation_id: str 

class ImageAnalysisResult(BaseModel):
    body: LLMMessage
    conversation_id: str 

common_system_message = SystemMessage("""
You can answer questions only about stock prices, machine learning, and azure services.
If the question is outside of the above domain, say that you can't answer the question.
Start your response with 'FinalResponse'.
""")


queue = asyncio.Queue[FinalResult]()
llm_results_dict = {}
condition = asyncio.Condition()


from autogen_core.application import SingleThreadedAgentRuntime
runtime = SingleThreadedAgentRuntime()

@default_subscription
@type_subscription("qa_agent")
class QAAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A Q&A Agent")
        self._model_client = model_client
        
        self._chat_history : List[LLMMessage]  = [SystemMessage("""
        You are AI assistant. You need to get the context needed to answer the question.
        Answer ONLY with the facts listed in the context below.
        <Context>
                                                                                                                        
        </Context>
        Provide citations and sources using the pageNumber and docName in the context in the format [Source: docName, Page No.: pageNumber]
        Do not generate answers that don't use the context below.
        """)]
    
    @message_handler
    async def handle_any_group_message(self, message: ToolResult, ctx: MessageContext) -> None:
        print("\033[32m" + "-" * 20 + "\033[0m")
        print(f"Received by QA Agent:{message.body}")

        self._chat_history.extend(message.body)
        completion = await self._model_client.create(self._chat_history)
        #print(f"Intermediate Response:{completion.content}")        
        im_result = message.body + [AssistantMessage(content=f"Response:{completion.content}", source="qa_agent")]
        await self.publish_message(IntermediateResult(body=im_result, conversation_id=message.conversation_id), DefaultTopicId())


@default_subscription
@type_subscription("evaluator_agent")
class EvalutorAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A Evalutor Agent")
        self._model_client = model_client
        
        self._chat_history : List[LLMMessage]  = [SystemMessage(
            """
        You are an Evaluator. You will be provided user question , context and Response.
        If the response is correct given the context and question, then format the response as Markdown and send it. 
        If the response is not correct, state that answer cannot be provided.
        
                                                                
        """)]
    
    @message_handler
    async def handle_any_group_message(self, message: IntermediateResult, ctx: MessageContext) -> None:
        print("\033[32m" + "-" * 20 + "\033[0m")
        print(f"Received by Evalutor Agent:{message.body}")
        self._chat_history.extend(message.body)
        completion = await self._model_client.create(self._chat_history)
        
        #print(completion.content)
        async with condition:
            llm_results_dict[message.conversation_id] = FinalResult(body=AssistantMessage(content=completion.content, source="evaluator_agent"), conversation_id=message.conversation_id)
            condition.notify_all()
        #await queue.put(FinalResult(body=AssistantMessage(content=completion.content, source="evaluator_agent")))
    
        del self._chat_history[1:]

from autogen_core.components.tool_agent import ToolAgent, tool_agent_caller_loop
from autogen_core.components.tools import FunctionTool, Tool, ToolSchema
@default_subscription
@type_subscription("tool_use_agent")
class ToolUseAgent(RoutedAgent):
    def __init__(self, model_client: AzureOpenAIChatCompletionClient, tool_schema: List[ToolSchema], tool_agent_type: str) -> None:
        super().__init__("An agent with tools")
        self._system_messages: List[LLMMessage] = [SystemMessage(
            """You are AI assistant. You should not answer the question directly. 
            You only need to call the tool provided to get the context needed to answer the question.
                For stock prices, use the tool get_stock_price.
                For Autocad architecture, machine learning and azure services, use the tool retrieve_search_results.
            Do not answer the question directly.
            """)]
        self._model_client = model_client
        self._tool_schema = tool_schema
        self._tool_agent_id = AgentId(tool_agent_type, self.id.key)
    
    @message_handler
    async def handle_any_group_message(self, message: ToolAgentMessage, ctx: MessageContext) -> None:
        print("\033[32m" + "-" * 20 + "\033[0m")
        print(f"Received by tool_use_agent:{message.body}")
        session: List[LLMMessage] =  self._system_messages + [message.body]
        messages = await tool_agent_caller_loop(
            self,
            tool_agent_id=self._tool_agent_id,
            model_client=self._model_client,
            input_messages=session,
            tool_schema=self._tool_schema,
            cancellation_token=ctx.cancellation_token,
        )
        # Return the final response.
        #assert isinstance(messages[-2].content[0], FunctionExecutionResult)
        #print(f"\n{'-'*80}\n tool result: {messages[-1].content}")
        formated_message = f"<Context>\n Tool name is: {messages[0].content[0].name}, tool input is: {messages[0].content[0].arguments} and tool result is: {messages[-2].content[0].content}\n</Context>"
        self._tool_result_history = [message.body] + [UserMessage(content=formated_message, source="tool_use_agent")]
        #session.append(UserMessage(content=formated_message, source="tool_use_agent"))
        await runtime.send_message(ToolResult(body=self._tool_result_history, conversation_id=message.conversation_id), AgentId("qa_agent", "default"))

@default_subscription
@type_subscription("ia_agent")
class ImageAnalysisAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A Image Analysis Agent")
        self._model_client = model_client
        
        self._chat_history : List[LLMMessage]  = [SystemMessage("""You are building and construction archtitect. 
            You need to analyze the image and describe the details like layout, size""")]
    
    @message_handler
    async def handle_any_group_message(self, message: ImageAnalysisMessage, ctx: MessageContext) -> None:
        self._chat_history.extend([message.body])
       
        completion = await self._model_client.create(self._chat_history)
        print(f"Image Analysis Response:{completion.content}")
        async with condition:
            llm_results_dict[message.conversation_id] = FinalResult(body=AssistantMessage(content=completion.content, source="ia_agent"), conversation_id=message.conversation_id)
            condition.notify_all()

@default_subscription
@type_subscription("group_chat_manager")
class GroupChatManager(RoutedAgent):
    def __init__(self, participant_topic_types: List[str]) -> None:
        super().__init__("Group chat manager")
        self._num_rounds = 0
        self._participant_topic_types = participant_topic_types
        self._chat_history: List[GroupChatMessage] = []

    @message_handler
    async def handle_message(self, message: GroupChatMessage, ctx: MessageContext) -> None:
        print("\033[32m" + "-" * 20 + "\033[0m")
        print(f"Received by GroupChatManager:{message.body}")
        self._chat_history.append(message)
        assert isinstance(message.body, UserMessage)
      
        speaker_topic_type = self._participant_topic_types[self._num_rounds % len(self._participant_topic_types)]
        self._num_rounds += 1
        #await self.publish_message(message, DefaultTopicId(type=speaker_topic_type))
        await runtime.publish_message(ToolAgentMessage(body=message.body, conversation_id=message.conversation_id), DefaultTopicId())



import random
from typing_extensions import Annotated
async def get_stock_price(ticker: str, date: Annotated[str, "Date in YYYY/MM/DD"]) -> float:
    # Returns a random stock price for demonstration purposes.
    return random.uniform(10, 200)


import search_helper
tools: List[Tool] = [FunctionTool(get_stock_price, description="Get the stock price."),
                     FunctionTool(search_helper.retrieve_search_results, description="""
                                  The index_name for the retrieve_search_results tool should either be the following and nothing else: 
                                    For Machine learning and Autocad Architecture related questions.
                                        index_name: aml_index_with_suggester
                                        search_query: user question
                                        or
                                    For Azure Services related questions like Azure Functions.
                                        index_name: vectest
                                        search_query: user question              
                                                    retrieve search results for user questions 
                                  on machine learning and azure services.""")]


async def register_agents():

    await ToolAgent.register(runtime, "tool_executor_agent", lambda: ToolAgent("tool executor agent", tools))
    await ToolUseAgent.register(
        runtime,
        "tool_use_agent",
        lambda: ToolUseAgent(
                get_model_client(), [tool.schema for tool in tools], "tool_executor_agent"
            ),
        )

    await QAAgent.register(
            runtime,
            "qa_agent",
            lambda: QAAgent(
                get_model_client(),
            ),
        )

    await EvalutorAgent.register(
                runtime,
                "evaluator_agent",
                lambda: EvalutorAgent(
                    get_model_client(),
                ),
            )
    
    await ImageAnalysisAgent.register(
            runtime,
            "ia_agent",
            lambda: ImageAnalysisAgent(
                get_model_client(),
            ),
        )
    
    await GroupChatManager.register(
            runtime,
            "group_chat_manager",
            lambda: GroupChatManager(
                participant_topic_types=["qa_agent" , "tool_use_agent", "evaluator_agent", "ia_agent"]
            ),
        )
    

#asyncio.run(register_agents())


async def start_multiagent_chat(user_message: str, image_url: str = None) -> str:
    
    try:
        start_time = time.time() 
        runtime.start()  
        end_time = time.time()

        elapsed_time_ms = (end_time - start_time) * 1000  # Convert to milliseconds

        print(f"runtime.start() took {elapsed_time_ms:.2f} ms.")
    except Exception as e:
        print(f"Error starting runtime: {e}")
        

    conversation_id = str(uuid.uuid4())
    
    if image_url:
        image_data = await Image.from_url(image_url)
        await runtime.send_message(ImageAnalysisMessage(body=UserMessage(content = [
            user_message,
            image_data
        ], source="user"), conversation_id=conversation_id), AgentId("ia_agent", "default"))
    else:
        await runtime.publish_message(
        GroupChatMessage(
            body=UserMessage(content=user_message, source="User"), conversation_id=conversation_id
        ),
        DefaultTopicId(),
        )
    #await runtime.send_message(StreamResponse(body=UserMessage(content=user_query3, source="user")), AgentId("qa_agent", "default"))
    #await runtime.stop_when_idle()
    group_chat_result = ""
    try:
        # Wait for a message in the queue, or you can use a timeout if needed
        #group_chat_result = (await queue.get()).body.content
        # clear queue 
        async with condition:
            while conversation_id not in llm_results_dict:
                await condition.wait()

            
            group_chat_result = llm_results_dict[conversation_id].body.content
            del llm_results_dict[conversation_id]
            print(f"conversation_id delete: {conversation_id}")
            print("\033[35m" + "-" * 20 + "\033[0m")
    except Exception as e:
        # Handle any exception that may occur during the wait for the response
        print(f"Error retrieving message from queue: {e}")
        group_chat_result = "An error occurred while waiting for the response."
    await runtime.stop()
    return group_chat_result

#print(asyncio.run(start_multiagent_chat("tell me about einstien.")))
