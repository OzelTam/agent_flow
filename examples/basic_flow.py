from agentflowpy import SimpleAgent, Context, AGENT_START, AGENT_END
# import logging

# logging.basicConfig(
#     level=logging.DEBUG, 
#     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
# )


# Create agent
agent = SimpleAgent[str]()

# Create context
ctx = Context[str](id="ctx1", messages=["hello"])

# Add context and switch to it
agent.add_context(ctx)

# Define flow steps
def start_step(context: Context[str]):
    print("Start step, messages:", context.messages)
    context.messages.append("from start_step")
    return "second_step" # Return next step tag

def second_step(context: Context[str]):
    print("Second step, messages:", context.messages)
    context.messages.append("finished")
    return AGENT_END # to end the flow or AGENT_START to create a loop

# Register steps
agent.register(start_step, tag=AGENT_START)
agent.register(second_step, tag="second_step")

# Run
agent.run("ctx1")

# After run
print("Final messages in context:", agent.contexts["ctx1"].messages)
# Expected output:
#   Start step, messages: ['hello']
#   Second step, messages: ['hello', 'from start_step']
# Final messages in context: ['hello', 'from start_step', 'finished']
