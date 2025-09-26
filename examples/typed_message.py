from pydantic import BaseModel, Field
from typing import Literal
from agentflowpy import SimpleAgent, Context, AGENT_START, AGENT_END
from dataclasses import dataclass, field
# from pydantic import BaseModel, Field

# #### MESSAGE AS RAW CLASS #####
# class Message:
#     def __init__(self, content:str, role:str="user"):
#         self.content = content
#         self.role = role
#     def __str__(self):
#         return f"Message(content={self.content}, role={self.role})"


#### MESSAGE AS DATACLASS #####
@dataclass
class Message:
    content:str
    role:str = field(default="user")


# ##### MESSAGE AS Pydantic BaseModel #####
# class Message(BaseModel):
#     content:str
#     role:str = Field(default="user")
    
def get_message(context: Context[Message]):
    msg = input("Enter your message (don't use 'badword'!): ")
    context.messages.append(Message(role="user", content=msg))
    return "filter_message"

def filter_message(context: Context[Message]):
    last_user_msg = next((m for m in reversed(context.messages) if m.role == "user"), None)
    is_bad = "badword" in last_user_msg.content.lower()
    msg_i = context.messages.index(last_user_msg)
    if is_bad:
        last_user_msg.content = last_user_msg.content.lower().replace("badword", "****")
        context.messages.append(Message(role="assistant", content="You have used a bad-word"))
        print("Message contained bad word")
    
    context.messages[msg_i] = last_user_msg
    return AGENT_END if is_bad else "chatbot" 

def chatbot(context: Context[Message]):
    last_user_msg = next((m for m in reversed(context.messages) if m.role == "user"), None)
    if last_user_msg:
        response = f"Echoing your message: {last_user_msg.content}" # Mock cahtbot functionality
    else:
        response = "Hello! How can I assist you today?"
    context.messages.append(Message(role="assistant", content=response))
    return AGENT_END


agent = SimpleAgent[Message]()

# Register steps
agent.register(func=get_message, tag=AGENT_START)
agent.register(func=filter_message, tag="filter_message")
agent.register(func=chatbot, tag="chatbot")


# Add Context
agent.add_context("cx", Context[Message]())

while True:
    agent.run("cx")
    print("Final message history:")
    for m in agent.get_context("cx").messages:
        print(">", m)
    print("\nNEW CYCLE STARTED")
