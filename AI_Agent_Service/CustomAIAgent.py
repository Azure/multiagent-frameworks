from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from typing import Any, Callable, Set, Dict, List, Optional
from azure.ai.projects.models import FunctionTool, ToolSet
import os

class CustomAIServiceAgent:
    _project_client : AIProjectClient
    _agent_instance: Any
    _model: str
    _agent_name: str
    _agent_instructions: str
    _tool_set : ToolSet
    _thread_id : str

    def __init__(self, agent_name: str, agent_instructions: str, tool_set: ToolSet, model: str = "gpt-4o-mini"):
        self._agent_name = agent_name
        self._project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(), conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )
        self._agent_instance = self._project_client.agents.create_agent(
            model=model, 
            name=agent_name,
            instructions=agent_instructions,
            toolset=tool_set
        )
        #thread = self._project_client.agents.create_thread()
        #self._thread_id = thread.id
    

    def post_message(self, message: str):
        message = self._project_client.agents.create_message(
            thread_id=self._thread_id,
            role="user",
            content=message,
        )
        #print("post_message: Agent Threadid: ", self._thread_id)
        run = self._project_client.agents.create_and_process_run(thread_id=self._thread_id, 
                                                                 assistant_id=self._agent_instance.id,
                                                                 max_completion_tokens=200,
                                                                 max_prompt_tokens=4000
                                                                 ) 
        if run.status == "failed":
            # Check if you got "Rate limit is exceeded.", then you want to get more quota
            print(f"Run failed: {run.last_error}")

        messages = self._project_client.agents.list_messages(thread_id=self._thread_id)
        last_msg = messages.get_last_text_message_by_role("assistant")
        if last_msg:
            #print(f"Agent id:{self._agent_instance.id} - Last Message: {last_msg.text.value}")
            return last_msg.text.value
        else:
            return None