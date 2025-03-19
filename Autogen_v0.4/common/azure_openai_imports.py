import os
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from common.autogen_imports import *
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

load_dotenv()

endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
deployed_model = os.environ["DEPLOYMENT_NAME"]


def get_ai_foundry_client() -> AzureAIChatCompletionClient:
    api_key = os.getenv("AI_FOUNDRY_MODEL_ENDPOINT_KEY", '')
    return AzureAIChatCompletionClient(
        endpoint=os.environ["AI_FOUNDRY_MODEL_ENDPOINT"],
        credential=AzureKeyCredential(api_key),
        model_info={
            "json_output": True,
            "function_calling": True,
            "vision": False,
            "family": "unknown",
        }
    )

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

def get_model_client_with_json() -> AzureOpenAIChatCompletionClient:
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
            "temperature":0.0,
            "response_format":{ "type": "json_object" }
        }
    )