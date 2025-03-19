import asyncio
from multi_agent_message_types import *

llm_results_dict = {}
condition = asyncio.Condition()


async def notify_result(message, llm_response):
    global llm_results_dict
    global condition
    async with condition:
        llm_results_dict[message.conversation_id] = FinalResult(body=AssistantMessage(content=llm_response, source="final_response"), conversation_id=message.conversation_id)
        condition.notify_all()



async def get_final_response(conversation_id):
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
    
    return group_chat_result