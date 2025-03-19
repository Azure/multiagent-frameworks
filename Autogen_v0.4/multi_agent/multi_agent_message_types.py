from pydantic import BaseModel
from autogen_core.models import ( 
    LLMMessage ,
    AssistantMessage 
    )


class FinalResult(BaseModel):
    body: LLMMessage