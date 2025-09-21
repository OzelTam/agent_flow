from agentflowpy import Context, Agent,  StepPass, AGENT_END, AGENT_START
# from dataclasses import dataclass, field
from pydantic import BaseModel, Field

##### MESSAGE AS RAW CLASS #####
# class Message:
#     def __init__(self, content:str, role:str="user"):
#         self.content = content
#         self.role = role
#     def __str__(self):
#         return f"Message(content={self.content}, role={self.role})"


##### MESSAGE AS DATACLASS #####
# @dataclass
# class Message:
#     content:str
#     role:str = field(default="user")


##### MESSAGE AS Pydantic BaseModel #####
class Message(BaseModel):
    content:str
    role:str = Field(default="user")
    

agent1 = Agent[Message]()

# add contexes 
agent1.context_manager.contexts["cx1"] = Context[Message]()
agent1.context_manager.contexts["cx2"] = Context[Message]()

# add messages
agent1.context_manager.contexts["cx1"].append(Message(content="Message to first context"))
agent1.context_manager.contexts["cx2"].append(Message(content="Message to second context"))

agent1.context_manager.switch_context("cx1")

state_dict = agent1.serialize_state() # Serialize as dictionary
state_json = agent1.serialize_state_json() # Serailize as json string

# Create another agent
agent2 = Agent[Message]()
agent2.restore_state_json(state_json, message_type=Message) # Restore from json string
# OR
# agent2.restore_state(state_dict, message_type=Message) # Restore from dict

for id, cx in agent2.context_manager.contexts.items():
    print(f"# MESSAGES OF '{id}'")
    print(f"{"\n".join([f"> {m}" for m in cx.messages])}\n")
 



