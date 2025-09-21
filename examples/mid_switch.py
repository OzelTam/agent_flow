from agent_flow import Context, Agent,  StepPass, AGENT_END, AGENT_START


agent = Agent[str]()
 
# add contexes 
agent.context_manager.contexts["cx1"] = Context[str]()
agent.context_manager.contexts["cx2"] = Context[str]() 

# set current context to "cx1"
agent.context_manager.switch_context("cx1")


def create_message(cx:Context[str]):
    message = "this is a message for 'cx1'"
    cx.messages.append(message) # Appends message to cx1
    agent.context_manager.switch_context("cx2") # Switch current_context to "cx2"
    return StepPass("append_message",
                    kwargs={"context_before":cx}, # Passes cx which is "cx1"  
                    refresh_context=True) # If refresh_context is false it will contiue passing "cx1" to first positional argument of next step

def append_message(cx:Context[str], context_before:Context[str]):
    last_msg_of_cx1 = context_before.messages[-1] # Get last message of context_before which passed down as kwarg
    cx.messages.append(f"Last Message of {context_before.id}: {last_msg_of_cx1}")
    return AGENT_END


agent.register_step(create_message, AGENT_START)
agent.register_step(append_message, "append_message")
agent.run()

for id, cx in agent.context_manager.contexts.items():
    print(f"# MESSAGES OF '{id}'")
    print(f"{"\n".join([f"> {m}" for m in cx.messages])}\n")
