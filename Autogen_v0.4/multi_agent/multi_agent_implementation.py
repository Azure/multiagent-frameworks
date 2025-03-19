import sys
import os

# Assuming the common folder is one level up
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)
print(parent_dir)

from common.azure_openai_imports import *
from multi_agent_tools import *
from agent_final_response_gatherer import *
from typing import List, Union
import json
from typing import Type
import uuid
import re

class GroupChatMessage(BaseModel):
    body: LLMMessage
    conversation_id: str

class TransactionInfo(BaseModel):
    body: List[LLMMessage]
    conversation_id: str
    

class AccountInfo(BaseModel):
    body: List[LLMMessage]
    conversation_id: str


class NeedMoreInfo(BaseModel):
    body: List[LLMMessage]
    conversation_id: str



class IntermediateResult(BaseModel):
    body: List[LLMMessage]
    conversation_id: str 

TransactionAccountInfo = Union[TransactionInfo, AccountInfo, NeedMoreInfo, IntermediateResult]

FinalResponderAgentMessage = Union[IntermediateResult, NeedMoreInfo]

class GroupChatMessages(BaseModel):
    body: List[LLMMessage]
    conversation_id: str



async def handle_transaction_account_info_message(self, message: List[LLMMessage], conversation_id: str, ctx: MessageContext) -> None:
    print("\033[32m" + "-" * 20 + "\033[0m")
    print(f"Received by {self._description}:{message}")

    session: List[LLMMessage] =  message
    messages = await tool_agent_caller_loop(
        self,
        tool_agent_id=self._tool_agent_id,
        model_client=self._model_client,
        input_messages=session,
        tool_schema=self._tool_schema,
        cancellation_token=ctx.cancellation_token,
    )
    
    if len(messages) < 2:
        # message[0] contains LLM response if tool result is not found
        self._chat_history.append(AssistantMessage(content=messages[0].content, source="tool_use_agent"))

    else:
        formated_message = f"""<Context>\n Tool name is: {messages[0].content[0].name}, 
                                tool input is: {messages[0].content[0].arguments} 
                                and tool result is: {messages[-2].content[0].content}\n</Context>"""
        self._chat_history.append(AssistantMessage(content=formated_message, source="tool_use_agent"))
   
    await self.publish_message(GroupChatMessages(body=[self._chat_history[-1]], conversation_id=conversation_id), DefaultTopicId("group_chat_any_topic", source=conversation_id))



@type_subscription(topic_type="Transify_support_topic")
class FinalResponderAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
            super().__init__("A Final Responder Agent")
            self._model_client = model_client
            
            self._chat_history : List[LLMMessage]  = [SystemMessage(content=
            """
            You are Transify Support reviewer agent. Transify is an online payment platform.
            You will be provided with Conversation History between users and multiple agents. 
            You need to review the conversation and provide the final response to the user.
            If the question has been answered correctly, state the complete answer. Otherwise ask the user for required information based on the conversation history.
            """)]
        
    @message_handler
    async def handle_missing_info(self, message: NeedMoreInfo, ctx: MessageContext) -> None:
        print("\033[32m" + "-" * 20 + "\033[0m")
        print(f"Received by {self._description}:{message.body}")
        await self.respond_to_user(message, ctx)

    @message_handler
    async def handle_any_group_message(self, message: IntermediateResult, ctx: MessageContext) -> None:
        print("\033[32m" + "-" * 20 + "\033[0m")
        print(f"Received by {self._description}:{message.body}")
        await self.respond_to_user(message, ctx)

    async def respond_to_user(self, message: IntermediateResult, ctx: MessageContext) -> None:
        self._chat_history.extend(message.body)
        completion = await self._model_client.create(self._chat_history)
        await notify_result(message, completion.content)
        del self._chat_history[1:]

@type_subscription(topic_type="Transify_support_topic")
class AccountInfoAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, tool_schema: List[ToolSchema], tool_agent_type: str) -> None:
        super().__init__("A Account Info Agent Agent")
        self._model_client = model_client
        self._system_message = SystemMessage(content="""
        You are Transify Support Agent. Transify is an online payment platform.
        You can provide information about the account details. 
        You need to know the 'account number' to provide the account details.
        If the 'account number' is provided use the get_account_info tool to get the account details.
        Format the response with 'Account Details:'.
        If the 'account number' is not provided, ask the user to provide the 'account number'.                                                      

        """)
        self._chat_history : List[LLMMessage]  = [self._system_message]
        self._model_client = model_client
        self._tool_schema = tool_schema
        self._tool_agent_id = AgentId(tool_agent_type, self.id.key)

    @message_handler
    async def handle_account_info_message(self, message: AccountInfo, ctx: MessageContext) -> None:
        self._chat_history.extend(message.body)
        await handle_transaction_account_info_message(self, self._chat_history, message.conversation_id, ctx)


@type_subscription(topic_type="Transify_support_topic")
class TransactionInfoAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, tool_schema: List[ToolSchema], tool_agent_type: str) -> None:
        super().__init__("A Transaction Info Agent Agent")
        self._model_client = model_client
        self._system_message = SystemMessage(content="""
        You are Transify Support Agent. Transify is an online payment platform.
        You can provide information about the transaction details for the account.
        You need to know the 'account number' to provide the transaction details.
        If the 'account number' is provided use the get_transaction_details tool to get the transaction details.
        Format the response with 'Transaction Details:'.
        If the 'account number' is not provided, ask the user to provide the 'account number'.                                                      

        """)
        self._chat_history : List[LLMMessage]  = [self._system_message]
        self._model_client = model_client
        self._tool_schema = tool_schema
        self._tool_agent_id = AgentId(tool_agent_type, self.id.key)
    
    @message_handler
    async def handle_transaction_info_message(self, message: TransactionInfo, ctx: MessageContext) -> None:
        self._chat_history.extend(message.body)
        await handle_transaction_account_info_message(self, self._chat_history, message.conversation_id, ctx)


@type_subscription(topic_type="group_chat_any_topic")
class GroupChatManager(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A group_chat agent")
        self._model_client = model_client
        self._system_message = SystemMessage(content=
        """
        You are a Transify Support Agent Manager. Transify is an online payment platform.
        You can help users with their Transify related queries. 
        You need to respond only to queries related to Transify and nothing else. 
        If the question is not related to Transify, state that you only respond to Transify related queries and cannot answer this question.        
        If this is Transify related question. you need to find the appropriate agent based on the question as below:
        Agent Types:
        
        1. AccountInfo: If the question is about account details.
        2. TransactionInfo: If the question is about transaction details.
        3. IntermediateResult: If the question has been answered and needs to be formatted and sent to the user.
        4. NeedMoreInfo: If you need more inputs from user to answer the question or cannot answer the question.

        Always respond in json format. DO NOT USE ```json or ``` in your response. 

        {"agentType": "One of the above agent types", "body": "user original question as json string."}

        """)
        self._chat_history : List[LLMMessage]  = [self._system_message]
        self._model_client = model_client
    
    def sanitize_json_string(self, json_str):
        # Remove or replace control characters (ASCII codes 0-31 and 127)
        sanitized_str = re.sub(r'[\x00-\x1f\x7f]', '', json_str)
        return sanitized_str

    @message_handler
    async def handle_group_messages(self, message: GroupChatMessages, ctx: MessageContext) -> None:
        self._chat_history.extend(message.body)
        completion = await self._model_client.create(self._chat_history)
        self._chat_history.append(UserMessage(content=completion.content, source="GroupChatManager"))
        print(f"from {self._description} completion: {completion.content}")
        
        sanitized_string = self.sanitize_json_string(completion.content)
        agent_type =  json.loads(sanitized_string)['agentType']        
        agent_class: Type[TransactionAccountInfo] = globals().get(agent_type)
        await self.publish_message(agent_class(body=self._chat_history[1:], conversation_id=message.conversation_id), DefaultTopicId(type="Transify_support_topic", source=message.conversation_id))




    @message_handler
    async def handle_user_message(self, message: GroupChatMessage, context: MessageContext)-> None:
        print(message)
        await self.handle_group_messages(GroupChatMessages(body=[message.body], conversation_id=message.conversation_id), context)



async def register_agents(runtime):
    await ToolAgent.register(runtime, "tool_executor_agent", lambda: ToolAgent("tool executor agent", tools))
    await AccountInfoAgent.register(
                runtime,
                "AccountInfoAgent",
                lambda: AccountInfoAgent(
                    get_model_client(), [tool.schema for tool in tools], "tool_executor_agent"
                ),
            )
    await TransactionInfoAgent.register(
            runtime,
            "TransactionInfoAgent",
            lambda: TransactionInfoAgent(
                get_model_client(), [tool.schema for tool in tools], "tool_executor_agent"
            ),
        )
    
    await FinalResponderAgent.register(
            runtime,
            "FinalResponderAgent",
            lambda: FinalResponderAgent(
                get_model_client()
            ),
        )

    await GroupChatManager.register(
            runtime,
            "GroupChatManager",
            lambda: GroupChatManager(
                get_model_client_with_json()      
                
                # Use Reasoning model DeepSeek R1
                # The output needs to be parsed to extract only the json part as the response contains "<think>reasoning details</think> final output." 
                #get_ai_foundry_client()           
            ),
        )


#runtime = SingleThreadedAgentRuntime()
#asyncio.run(register_agents(runtime))   



async def run_agents(runtime):
    runtime.start()
    conversation_id = str(uuid.uuid4())
    try:
        #await runtime.publish_message(GroupChatMessage(body=UserMessage(content="I want to know my credit card balance.", source="user"), conversation_id=conversation_id), DefaultTopicId(type="group_chat_any_topic", source=conversation_id)) 
        await runtime.publish_message(GroupChatMessage(body=UserMessage(content="I want to know my credit card balance. My account number is A1234567890 ", source="user"), conversation_id=conversation_id), DefaultTopicId(type="group_chat_any_topic", source=conversation_id)) 
        await runtime.stop_when_idle()
    except Exception as e:
        print(f"Error in publishing message: {e}")
    

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
            print(f"conversation_id: {conversation_id}")
            print("\033[35m" + "-" * 20 + "\033[0m")
    except Exception as e:
        # Handle any exception that may occur during the wait for the response
        print(f"Error retrieving message from queue: {e}")
        group_chat_result = "An error occurred while waiting for the response."

    print(group_chat_result)
    #agent_response = await runtime.send_message(TransifyHelpAgentAMessage(body=UserMessage(content="Plan a 3 day road trip to zion national park", source="user")), recipient=AgentId(type="TransifyHelpAgent", key="Transify_user1")) 
    #print(agent_response)
    #agent_response = await runtime.send_message(TransifyHelpAgentAMessage(body=UserMessage(content="how to report Fraud", source="user")), recipient=AgentId(type="TransifyHelpAgent", key="Transify_user1")) 
    #print(agent_response)

#asyncio.run(run_agents(runtime))
