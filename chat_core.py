import os
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, AIMessage
from config import GROQ_API_KEY, MODEL_NAME

os.environ["GROQ_API_KEY"] = GROQ_API_KEY
llm = ChatGroq(temperature=0, model_name=MODEL_NAME)

# Short-term memory: last N messages
MEMORY_SIZE = 5

def get_response(messages):
    # Keep last MEMORY_SIZE messages for context
    recent_messages = messages[-MEMORY_SIZE:]
    human_ai_messages = []
    for msg in recent_messages:
        if msg["role"] == "user":
            human_ai_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            human_ai_messages.append(AIMessage(content=msg["content"]))
    try:
        return llm(human_ai_messages).content
    except Exception as e:
        return f"Error: {e}"
