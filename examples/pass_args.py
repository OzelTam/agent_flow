from agentflowpy import Agent, Context, ContextManager, StepPass, AGENT_START, AGENT_END

ctx = Context[str](id="ctx1")
agent = Agent[str]()
agent.context_manager.switch_context(ctx)

def ask_name(context: Context[str]):
    name = input("What is your name? ")
    context.append(f"user_name: {name}")
    # Use StepPass to pass name to next ("greet") step 
    return StepPass(step="greet", kwargs={"name": name})
    # or use positional args like:
    return StepPass(step="greet", args=(name,))

def greet(context: Context[str], name: str):
    greeting = f"Hello, {name}!"
    context.append(greeting)
    return AGENT_END

agent.register_step(ask_name, tag=AGENT_START) # Starting step
agent.register_step(greet, tag="greet")

agent.run()

print("Conversation messages:", agent.context_manager.current_context.messages)