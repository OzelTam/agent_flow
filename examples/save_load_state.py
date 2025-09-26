from agentflowpy import Context, SimpleAgent,  StepLead, AGENT_END, AGENT_START
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
    

agent1 = SimpleAgent[Message]()

# add contexes 
agent1.add_context("cx1", Context[Message]())
agent1.add_context("cx2", Context[Message]())

# add messages
agent1.contexts["cx1"].messages.append(Message(content="Message to first context"))
agent1.contexts["cx2"].messages.append(Message(content="Message to second context"))


state_dict = agent1.contexts_to_dicts() # Serialize as dictionary

# Create another agent
contexts = SimpleAgent[Message].contexts_from_dicts(state_dict, msg_type=Message)
agent2 = SimpleAgent[Message]()
agent2.add_contexts(contexts)


for id, cx in agent2.contexts.items():
    print(f"# MESSAGES OF '{id}'")
    print(f"{"\n".join([f"> {m}" for m in cx.messages])}\n")
 



