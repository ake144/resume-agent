from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage


user_memory = {}


def get_user_memory(user_id:str) -> dict:
    if user_id not in user_memory:
        user_memory[user_id] =  ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )
    return user_memory[user_id]

async def add_to_memory(user_id:str, message:str, role:str="user"):
    memory = get_user_memory(user_id)
    if role == "user":
        memory.chat_memory.add_message(HumanMessage(content=message))
    else:
        memory.chat_memory.add_message(AIMessage(content=message))