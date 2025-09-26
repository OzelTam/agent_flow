from agentflowpy import SimpleAgent, Context, StepLead, AGENT_START, AGENT_END

agent = SimpleAgent[str]()
agent.add_context(Context[str](id="ctx1"))

def ask_name(context: Context[str]):
    name = input("What is your name? ")
    context.messages.append(f"user_name: {name}")
    # Use StepLead to pass name to next ("greet") step 
    return StepLead(step="greet", kwargs={"name": name})
    # or use positional args like:
    return StepLead(step="greet", args=(name,))

def greet(context: Context[str], name: str):
    greeting = f"Hello, {name}!"
    context.messages.append(greeting)
    return AGENT_END

agent.register(ask_name, tag=AGENT_START) # Starting step
agent.register(greet, tag="greet")

agent.run("ctx1")

print("Conversation messages:", agent.contexts["ctx1"].messages)