from pydantic import BaseModel, Field
from typing import Literal
from agentflowpy import Agent, Context, AGENT_START, AGENT_END, StepPass

class Message(BaseModel):
    role: Literal["user", "system", "assistant"] = Field(default="user")
    content: str
    
def get_message(context: Context[Message]):
    msg = input("Enter your message (don't use 'badword'!): ")
    context.append(Message(role="user", content=msg))
    return "filter_message"

def filter_message(context: Context[Message]):
    last_user_msg = next((m for m in reversed(context.messages) if m.role == "user"), None)
    is_bad = "badword" in last_user_msg.content.lower()
    msg_i = context.index(last_user_msg)
    if is_bad:
        last_user_msg.content = last_user_msg.content.lower().replace("badword", "****")
        context.append(Message(role="assistant", content="You have used a bad-word"))
        print("Message contained bad word")
    
    context[msg_i] = last_user_msg
    return AGENT_END if is_bad else "chatbot" 

def chatbot(context: Context[Message]):
    last_user_msg = next((m for m in reversed(context.messages) if m.role == "user"), None)
    if last_user_msg:
        response = f"Echoing your message: {last_user_msg.content}" # Mock cahtbot functionality
    else:
        response = "Hello! How can I assist you today?"
    context.append(Message(role="assistant", content=response))
    return AGENT_END


agent = Agent[Message]()
# Register steps
agent.register_step(func=get_message, tag=AGENT_START)
agent.register_step(func=filter_message, tag="filter_message")
agent.register_step(func=chatbot, tag="chatbot")


# Create and set Context
cx = Context[Agent]()
agent.context_manager.switch_context(cx) 

while True:
    agent.run()
    print("Final message history:")
    for m in agent.context_manager.current_context.messages:
        print(">", m)
    print("\nNEW CYCLE STARTED")
