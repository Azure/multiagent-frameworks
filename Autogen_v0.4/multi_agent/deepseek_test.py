import os
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

api_key = "pMH2yJSwccN38GZ0bUnB6aUzH0hHUJyn" #os.getenv("AZURE_INFERENCE_CREDENTIAL", '')
if not api_key:
  raise Exception("A key should be provided to invoke the endpoint")

client = ChatCompletionsClient(
    endpoint='https://DeepSeek-R1-snkcj.westus3.models.ai.azure.com',
    credential=AzureKeyCredential(api_key)
)

model_info = client.get_model_info()
print("Model name:", model_info.model_name)
print("Model type:", model_info.model_type)
print("Model provider name:", model_info.model_provider_name)

payload = {
  "messages": [
    {
      "role": "system",
      "content": """You are a Transify Support Agent Manager. Transify is an online payment platform.
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

        {"agentType": "One of the above agent types", "body": "user original question as json string."}"""
    },
    
    {
      "role": "user",
      "content": "I want to know my credit card balance."
    }
  ],
  "max_tokens": 2048
}
response = client.complete(payload)

print("Response:", response.choices[0].message.content)
print("Model:", response.model)
print("Usage:")
print("	Prompt tokens:", response.usage.prompt_tokens)
print("	Total tokens:", response.usage.total_tokens)
print("	Completion tokens:", response.usage.completion_tokens)