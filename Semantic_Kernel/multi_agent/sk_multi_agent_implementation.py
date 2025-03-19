from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import ChatCompletionAgent, AgentGroupChat
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
import json
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.agents.strategies import (
    KernelFunctionSelectionStrategy,
    KernelFunctionTerminationStrategy,
)

from multi_agent_tools import MultiAgentToolsPlugin



class MultiAgent:
    def __init__(self):
        self.multi_agent_plugin = MultiAgentToolsPlugin()
        self.group_chat = self._create_group_chat_with_agents()

    def _create_kernel_with_chat_completion(self, service_id: str) -> Kernel:
        kernel = Kernel()
        kernel.add_service(AzureChatCompletion(service_id=service_id))
        return kernel

    def _initialize_agent_with_plugin(self, service_id: str, agent_name: str, instructions: str) -> Kernel:
        """
        Initialize a chat completion agent with the given service ID, agent name, and instructions.
        """
        kernel = Kernel()
        try:
            kernel.add_service(AzureChatCompletion(service_id=service_id))
            kernel.add_plugin(self.multi_agent_plugin, plugin_name="MultiAgentToolsPlugin")
            settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
            settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

            sk_agent = ChatCompletionAgent(
                service_id=service_id,
                kernel=kernel,
                name=agent_name,
                instructions=instructions,
                execution_settings=settings
            )
            return sk_agent
        except Exception as e:
            raise RuntimeError(f"Error initializing agent: {e}")

    def _create_group_chat_with_agents(self):
        get_account_info_agent = self._initialize_agent_with_plugin(
            service_id="get_account_info_agent",
            agent_name="get_account_info_agent",
            instructions="""You are Transify Support Agent. Transify is an online payment platform.
                You can provide information about the account details such as credit card balance. 
                You need to know the 'account number' to provide the account details.
                If the 'account number' is provided use the get_account_info tool to get the account details.
                Format the response with 'Account Details:'.
                If the 'account number' is not provided, ask the user to provide the 'account number'.
            """
        )

        get_transaction_info_agent = self._initialize_agent_with_plugin(
            service_id="get_transaction_info_agent",
            agent_name="get_transaction_info_agent",
            instructions="""You are Transify Support Agent. Transify is an online payment platform.
                You can provide information about the transaction details for the account.
                You need to know the 'account number' to provide the transaction details.
                If the 'account number' is provided use the get_transaction_details tool to get the transaction details.
                Format the response with 'Transaction Details:'.
                If the 'account number' is not provided, ask the user to provide the 'account number'.
            """
        )

        final_responder_agent = self._initialize_agent_with_plugin(
            service_id="final_responder_agent",
            agent_name="final_responder_agent",
            instructions="""You are Transify Support reviewer agent. Transify is an online payment platform.
                You will be provided with Conversation History between users and multiple agents. 
                Answer the user question only if it is about account details or transaction details for Transify. 
                You need to review the conversation and provide the final response to the user.
                If the question has been answered correctly, state the complete answer. Otherwise ask the user for required information based on the conversation history.
            """
        )

        termination_function = KernelFunctionFromPrompt(
        function_name="termination",
        prompt="""
        If the user questions is not about account details or transaction details for Transify, 
        The conversation should be terminated with "N/A. This is not a Transify related question. 
        Please ask a question about account details or transaction details for Transify."

        History:
        {{$history}}
        """,
        )

        selection_function = KernelFunctionFromPrompt(
        function_name="selection",
        prompt=f"""
        The user question should only be about account details or transaction details for Transify and nothing else.
        Do not answer the user question if it is not about account details or transaction details for Transify.
        Determine which participant takes the next turn in a conversation based on the the most recent participant.
        State only the name of the participant to take the next turn.
        No participant should take more than one turn in a row.

        Choose only from these participants:
        - get_account_info_agent
        - get_transaction_info_agent
        - final_responder_agent

       

        History:
        {{{{$history}}}}
        """,
        )

        return AgentGroupChat(
            agents=[get_account_info_agent, get_transaction_info_agent, final_responder_agent],
            termination_strategy=KernelFunctionTerminationStrategy(
            agents=[final_responder_agent],
            function=termination_function,
            kernel=self._create_kernel_with_chat_completion("termination"),
            result_parser=lambda result: str(result.value[0]).lower().find("n/a") == 0,
            history_variable_name="history",
            maximum_iterations=10,
            ),
            selection_strategy=KernelFunctionSelectionStrategy(
            function=selection_function,
            kernel=self._create_kernel_with_chat_completion("selection"),
            result_parser=lambda result: str(result.value[0]) if result.value is not None else "final_responder_agent",
            #agent_variable_name="agents",
            history_variable_name="history",
            ),
        )
    
        
        

    async def start_multi_agent_chat(self, user_input: str):
        await self.group_chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=user_input))


        try:

            if self.group_chat.is_complete:
                self.group_chat.is_complete = False
                
            async for content in self.group_chat.invoke():
                #print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
                return content.content
        except Exception as e:
            print("Error in multi agent chat: ", e)

class MultiAgentSessionManager:
    def __init__(self):
        self.sessions = {}

    def get_or_create_session(self, conversation_id: str) -> MultiAgent:
        """
        Retrieve an existing MultiAgent instance for the given conversation_id.
        If not found, create a new instance and store it.
        """
        if conversation_id not in self.sessions:
            print(f"session with {conversation_id} not found")
            self.sessions[conversation_id] = MultiAgent()

        return self.sessions[conversation_id]