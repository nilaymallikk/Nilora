from agent import get_agent
from langchain_core.messages import HumanMessage

agrnt = get_agent("gemini-2.5-flash")

config = {
    "configurable": {
        "thread_id": "test-thered-id"
    }
}

for message_chunk, metadata in agrnt.stream(
    {"messages": [HumanMessage(content="Tell me about latest news in ai")]}, 
    config=config,
    stream_mode="messages"
    ):

    if message_chunk.content:
        print(message_chunk.content, end="", flush=True)
    