from agentflowpy import Agent, Context, ContextManager, AGENT_START, AGENT_END



# Create agent
agent = Agent[str]()

# Create context
ctx = Context[str](id="ctx1", messages=["hello"])

# Add context and switch to it
agent.context_manager.current_context = ctx 
# or agent.context_manager.switch_context(ctx1)


# Define flow steps
def start_step(context: Context[str]):
    print("Start step, messages:", context.messages)
    context.append("from start_step")
    return "second_step" # Return next step tag

def second_step(context: Context[str]):
    print("Second step, messages:", context.messages)
    context.append("finished")
    return AGENT_END # to end the flow or AGENT_START to create a loop

# Register steps
agent.register_step(start_step, tag=AGENT_START)
agent.register_step(second_step, tag="second_step")

# Run
agent.run()

# After run
print("Final messages in context:", agent.context_manager.current_context.messages)
# Expected output:
#   Start step, messages: ['hello']
#   Second step, messages: ['hello', 'from start_step']
# Final messages in context: ['hello', 'from start_step', 'finished']
