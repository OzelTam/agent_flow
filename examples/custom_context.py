from agentflowpy import Context, Agent, AGENT_START
from dataclasses import dataclass

@dataclass
class Message:
    content:str
    role:str = "user"

class CustomContext(Context[Message]):
    def __init__(self, username:str, id = None, messages = None):
        super().__init__(id, messages)
        self.username = username

    def to_dict(self): # Override to_dict to include extra fields
        result = super().to_dict()
        result["username"] = self.username
        return result
    
    @classmethod
    def from_dict(cls, dict, message_type): # Override from_dict to create self.
        s = super().from_dict(dict, message_type)
        username = dict.get("username", None)
        return  CustomContext(username, s.id, s.messages)


agent = Agent[Message, CustomContext]()

agent.add_context("cx",CustomContext(""))


def get_print_message(cx:CustomContext):
    if cx.username == "":
        name = input("Please enter your username: ")
        cx.username = name
    message = input("Enter your message: ")
    cx.messages.append(Message(message))
    print(f"{cx.username} entered following message: {cx.messages[-1]}")
    return AGENT_START


agent.register(get_print_message, AGENT_START)


agent.run("cx")
