from agentflowpy import Context, SimpleAgent,  StepLead, AGENT_END, AGENT_START


agent = SimpleAgent[str]()
 
# add contexes 
agent.add_context("cx1",Context[str]())
agent.add_context("cx2",Context[str]())

def create_message(cx:Context[str]):
    cx.messages.append("this is a message for 'cx1'") # Appends message to cx1
    return StepLead("append_message",
                    kwargs={"context_before":cx}, # Passes cx which is "cx1"  
                    modify_flow_context="cx2") # If refresh_context is false it will contiue passing "cx1" to first positional argument of next step

def append_message(cx:Context[str], context_before:Context[str]):
    last_msg_of_cx1 = context_before.messages[-1] # Get last message of context_before which passed down as kwarg
    cx.messages.append(f"Last Message of {context_before.id}: {last_msg_of_cx1}")
    return AGENT_END


agent.register(create_message, AGENT_START)
agent.register(append_message, "append_message")
agent.run("cx1")

for id, cx in agent.contexts.items():
    print(f"# MESSAGES OF '{id}'")
    print(f"{"\n".join([f"> {m}" for m in cx.messages])}\n")
