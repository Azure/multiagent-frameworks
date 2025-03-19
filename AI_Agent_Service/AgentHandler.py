import json
from azure.ai.projects import AIProjectClient
from CustomAIAgent import CustomAIServiceAgent
from typing import Dict, Optional
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel
import os

class CustomAIAgentResponse(BaseModel):
    agent_name: str
    agent_response: str

class AgentHandler:
    _project_client : AIProjectClient
    _agents: Dict[str, CustomAIServiceAgent] = {}
    _thread_id : str
    _last_agent_response: str
    _agent_handler_instructions: str = """
    
    
    You are a Transify Support Agent Manager. Transify is an online payment platform.
    You can help users with their Transify related queries. 
    You need to respond only to queries related to Transify and nothing else.
    You need to answer end user questions using the agents provided below. 
    Each agent has a specific area of expertise and tools to help you answer questions.
    Based on the user question you need to idenfity the correct agent who can help answer the question.

    Team Members:

        1. GetAccountInfoAgent: If the question is about account details such as account info and balance.
        2. GetTransactionDetailsAgent: If the question is about transaction details such as latest transaction.
        3. UnknownAgent: If the question is not related to Transify.
        
    
    Respond in the json format below: Dont add ```json or ``` in the response or .

    {
        "agent_name" : "AgentName",
        "agent_response" : "Determine the input needed for the agent based on previous conversation."
        
    }
    """

    def __init__(self):
        self._project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(), conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )
        thread = self._project_client.agents.create_thread()
        self._thread_id = thread.id
    

    def add_agent(self, agent_instance: CustomAIServiceAgent):
        agent_instance._thread_id = self._thread_id
        #print("add_agent: AgentHandler Threadid: ", self._thread_id)
        self._agents[agent_instance._agent_name] = agent_instance
    

    def identify_agent(self, message: str) -> Optional[CustomAIServiceAgent]:
        
        handler_agent = CustomAIServiceAgent("AgentHandler", self._agent_handler_instructions, None, model="gpt-4o")
        handler_agent._thread_id = self._thread_id
        next_agent_name = handler_agent.post_message(message)
        parsed_json = json.loads(next_agent_name)
        agent_response = CustomAIAgentResponse(**parsed_json)
        #print(f"Next Agent is : {agent_response.agent_name}")
        for agent_name, agent_instance in self._agents.items():
            #print(f"Agent Name in list: {agent_name}")
            if agent_name.lower() == agent_response.agent_name.lower():
                return agent_instance
        return None

    def answer_user_question(self, message:str):
        agent_instance = self.identify_agent(message)
        if agent_instance:
            #print(f"Agent identified: {agent_instance._agent_name}")
            return agent_instance.post_message(message)
        else:
            return "I can only answer questions about Transify account and transaction details."