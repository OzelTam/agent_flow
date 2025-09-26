from agentflowpy import Agent, Context, StepLead, AGENT_START, AGENT_END
import asyncio

def test_context_registration():
    agent = Agent[str, Context[str]]()
    CX_ID = "cx1"

    agent.add_context(CX_ID, Context[str]())
    assert len(agent.contexts) == 1  # Context registration test

    agent.add_context(Context[str]())
    assert len(agent.contexts) == 2  # Context registration overloaded test

def test_function_registration():
    agent = Agent[str, Context[str]]()

    def sample(cx: Context[str]):
        cx.messages.append("Hello")

    def sample1(cx: Context[str], msg):
        cx.messages.append(msg or "Hi")

    agent.register(sample, AGENT_START)
    assert len(agent.registered_functions) == 1  # Function registration test

    agent.register(sample1)
    assert any(f.__name__ == "sample1" for f in agent.registered_functions.values())

def test_get_context():
    agent = Agent[str, Context[str]]()
    CX_ID = "cx1"
    agent.add_context(CX_ID, Context[str]())
    cx = agent.get_context(CX_ID)
    assert cx.id == CX_ID  # get_context test

def test_run_default():
    agent = Agent[str, Context[str]]()
    CX_ID = "cx1"
    agent.add_context(CX_ID, Context[str]())

    def sample(cx: Context[str]):
        cx.messages.append("Hello")

    agent.register(sample, AGENT_START)
    cx = agent.get_context(CX_ID)

    agent.run(CX_ID)
    assert cx.messages == ["Hello"]  # Default run test

def test_run_with_steps():
    agent = Agent[str, Context[str]]()
    CX_ID = "cx1"
    agent.add_context(CX_ID, Context[str]())

    def sample(cx: Context[str]):
        cx.messages.append("Hello")

    def sample1(cx: Context[str], msg = None):
        cx.messages.append(msg or "Hi")

    agent.register(sample, AGENT_START)
    agent.register(sample1)
    cx = agent.get_context(CX_ID)

    # first run initializes with sample
    agent.run(CX_ID)
    # run sample1 in different ways
    agent.run(cx, StepLead(sample1.__name__))
    agent.run(cx, StepLead(sample1.__name__, args=("Ha",)))
    agent.run(cx, StepLead(sample1.__name__, kwargs={"msg": "Ho"}))

    assert cx.messages == ["Hello", "Hi", "Ha", "Ho"]

async def test_arun_default():
    agent = Agent[str, Context[str]]()
    CX_ID = "cx1"
    agent.add_context(CX_ID, Context[str]())

    async def sample(cx: Context[str]):
        await asyncio.sleep(0.1)
        cx.messages.append("Hello")

    agent.register(sample, AGENT_START)
    cx = agent.get_context(CX_ID)

    await agent.arun(CX_ID)
    assert cx.messages == ["Hello"]  # Default run test

async def test_arun_with_steps():
    agent = Agent[str, Context[str]]()
    CX_ID = "cx1"
    agent.add_context(CX_ID, Context[str]())

    async def sample(cx: Context[str]):
        await asyncio.sleep(0.1)
        cx.messages.append("Hello")

    async def sample1(cx: Context[str], msg = None):
        await asyncio.sleep(0.1)
        cx.messages.append(msg or "Hi")

    agent.register(sample, AGENT_START)
    agent.register(sample1)
    cx = agent.get_context(CX_ID)

    # first run initializes with sample
    await agent.arun(CX_ID)
    # run sample1 in different ways
    await agent.arun(cx, StepLead(sample1.__name__))
    await agent.arun(cx, StepLead(sample1.__name__, args=("Ha",)))
    await agent.arun(cx, StepLead(sample1.__name__, kwargs={"msg": "Ho"}))

    assert cx.messages == ["Hello", "Hi", "Ha", "Ho"]

def test_serialize_restore():
    from dataclasses import dataclass
    @dataclass
    class Msg:
        content:str
        role:str = "user"
        
    agent = Agent[Msg, Context[Msg]]()
    agent.add_context("cx",Context[Msg](messages=[Msg("Hello")]))
    
    dcts = agent.contexts_to_dicts()
    
    assert len(dcts) == 1
    assert dcts[0]["id"] == "cx"
    assert len(dcts[0]["messages"]) == 1
    
    cxes = Agent[Msg, Context[Msg]].contexts_from_dicts(dcts, Msg)
    
    assert len(cxes) == 1
    assert len(cxes[0].messages) == 1
    assert isinstance(cxes[0].messages[0], Msg)
    assert cxes[0].messages[0] == Msg("Hello")
    
    ag2 = Agent[Msg, Context[Msg]]()
    ag2.add_contexts(cxes)
    
    assert len(ag2.contexts) == 1
    ag2.remove_context("cx")
    # ag2.clear_contexts()
    assert len(ag2.contexts) == 0
    
def test_custom_context():
    from dataclasses import dataclass
    @dataclass
    class Msg:
        content:str
        role:str = "user"
    
    class CustomCx(Context[Msg]):
        def __init__(self,extra:str, id = None, messages = None):
            super().__init__(id, messages)
            self.extra = extra

        def to_dict(self):
            d = super().to_dict()
            d["extra"] = self.extra
            return d
        
        @classmethod
        def from_dict(self, dict, message_type):
            c = super().from_dict(dict, message_type)
            xtra = dict.get("extra", None)
            return CustomCx(xtra, c.id, c.messages)
        
    agent = Agent[Msg, CustomCx]()
    agent.add_context("cc", CustomCx("EXTRA"))
    assert agent.get_context("cc").extra == "EXTRA"

    agent.get_context("cc").messages.append(Msg("Hello"))
    
    
    # Serialization
    cc_dcts = agent.contexts_to_dicts()
    assert len(cc_dcts) == 1
    assert cc_dcts[0]["extra"] == "EXTRA"
    
    # Deserialization
    ccs =  Agent[Msg, CustomCx].contexts_from_dicts(cc_dcts, Msg, CustomCx)
    assert len(ccs) == 1
    assert ccs[0].extra == "EXTRA"
    assert isinstance(ccs[0], CustomCx)
    assert len(ccs[0].messages) == 1
    assert ccs[0].messages[0] == Msg("Hello") 

def test_mid_change():
    cx1 = Context[str]()
    cx2 = Context[str]()
    agent = Agent()
    agent.add_context("cx1", cx1)
    agent.add_context("cx2", cx2)
    
    def start(cx:Context[str]):
        cx.messages.append("start")
        return StepLead("end", modify_flow_context="cx2")
    def end(cx:Context[str]):
        cx.messages.append("end")
        return AGENT_END
        
    agent.register(start, AGENT_START)
    agent.register(end)
    agent.run("cx1")
    
    assert cx1.messages == ["start"]
    assert cx2.messages == ["end"]