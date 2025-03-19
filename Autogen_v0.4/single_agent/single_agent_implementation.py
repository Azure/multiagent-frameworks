import sys
import os

# Assuming the common folder is one level up
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)
print(parent_dir)

from common.azure_openai_imports import *



class transifyHelpAgentAMessage(BaseModel):
    body: LLMMessage


@type_subscription(topic_type="transify_help_topic")
class transifyHelpAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient):
        super().__init__("A transify Help Agent")        
        self._model_client = model_client
        self._system_message = SystemMessage(content=
        """
        You are a transify Help Agent. Transify is an online payment platform.
        You can help users with their transify related queries. 
        You need to respond only to queries related to transify and nothing else. 
        If the question is not related to transify, state that you only respond to transify related queries and cannot answer this question.        

        """)
        self._chat_history : List[LLMMessage]  = [self._system_message]

    @message_handler
    async def respond_to_user_question(self, message: transifyHelpAgentAMessage, context: MessageContext) -> str:
        self._chat_history.append(message.body)
        completion = await self._model_client.create(self._chat_history)
        self._chat_history.extend([AssistantMessage(content=f"{completion.content}", source="transifyHelpAgent")])
        return completion.content

runtime = SingleThreadedAgentRuntime()

async def register_agents(runtime):

    await transifyHelpAgent.register(
        runtime, 
        "transifyHelpAgent",
        lambda: transifyHelpAgent(get_model_client())
    )


#asyncio.run(register_agents(runtime))

async def run_agents():
    runtime.start()
    #agent_response = await runtime.send_message(
    #    transifyHelpAgentAMessage(
    #        body=UserMessage(content="What are payment reversals and how to avoid them", 
    #              source="user")), recipient=AgentId(type="transifyHelpAgent", key="transify_user1")) 
    
    agent_response = await runtime.send_message(
    transifyHelpAgentAMessage(
        body=UserMessage(content="What are payment reversals and how to avoid them", source="user")
    ), 
    recipient=AgentId(type="transifyHelpAgent", key="transify_user1"))


    print(agent_response)
#    agent_response = await runtime.send_message(transifyHelpAgentAMessage(body=UserMessage(content="Plan a 3 day road trip to zion national park", source="user")), recipient=AgentId(type="transifyHelpAgent", key="transify_user1")) 
#    print(agent_response)
#    agent_response = await runtime.send_message(transifyHelpAgentAMessage(body=UserMessage(content="how to report Fraud", source="user")), recipient=AgentId(type="transifyHelpAgent", key="transify_user1")) 
#    print(agent_response)
#
#asyncio.run(run_agents())