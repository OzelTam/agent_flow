import pytest
import json
from agentflowpy.agent import Agent, StepPass, AGENT_START, AGENT_END, _resrore_cx_msg_types
from agentflowpy.context import Context
from agentflowpy.context_manager import ContextManager
import asyncio


def test_with_async():
    agent = Agent[str]()
    ctx = Context[str]()
    agent.context_manager.switch_context(ctx)
    async def mock_start(cx:Context[str]):
        await asyncio.sleep(2)
        ctx.append("Hi")
        
    agent.register_step(mock_start, AGENT_START)
    agent.run()
    
    assert agent.context_manager.current_context.messages == ["Hi"]
        

def test_agent_initializes_context_manager():
    agent = Agent[str]()
    assert isinstance(agent.context_manager, ContextManager)

def test_run_with():
    agent = Agent[str]()
    ctx = Context[str]()
    agent.context_manager.switch_context(ctx)
    def add_msg(cx:Context[str], msg:str):
        ctx.append(msg)
    def mock_start(cx:Context[str]):
        return AGENT_END
    
    agent.register_step(mock_start, AGENT_START)
    agent.register_step(add_msg, "add_msg")
    
    agent.run(entry_point="add_msg", args=("hey",))
    assert ctx.messages == ["hey"]
    agent.run(entry_point="add_msg", kwargs={"msg":"you"})
    assert ctx.messages == ["hey", "you"]
    
    
    
def test_register_step_and_run_simple():
    agent = Agent[str]()
    ctx = Context[str](id="c1", messages=["start"])
    agent.context_manager.contexts["c1"] = ctx
    agent.context_manager.switch_context("c1")

    def first_step(context: Context[str]):
        return AGENT_END

    agent.register_step(first_step, AGENT_START)
    agent.run()  # Should not raise
    assert agent.context_manager.current_context.id == "c1"


def test_add_duplicate_step_raises():
    agent = Agent[str]()
    agent.register_step(lambda ctx: AGENT_END, "s1")
    with pytest.raises(ValueError):
        agent.register_step(lambda ctx: AGENT_END, "s1")


def test_run_without_context_raises():
    agent = Agent[str]()
    with pytest.raises(ValueError):
        agent.run()


def test_run_with_step_pass():
    agent = Agent[str]()
    ctx = Context[str](id="c1", messages=["start"])
    agent.context_manager.contexts["c1"] = ctx
    agent.context_manager.switch_context("c1")

    def step1(context: Context[str]):
        return StepPass(step="step2", refresh_context=True)

    def step2(context: Context[str]):
        return AGENT_END

    agent.register_step(step1, "step1")
    agent.register_step(step2, "step2")

    agent.run()
    assert ctx in agent.context_manager.contexts.values()


def test_serialize_and_restore_state():
    agent = Agent[str]()
    ctx = Context[str](id="c1", messages=["msg"])
    agent.context_manager.contexts["c1"] = ctx
    agent.context_manager.switch_context("c1")

    state = agent.serialize_state()
    new_agent = Agent[str]()
    new_agent.restore_state(state, str)

    assert "c1" in new_agent.context_manager.contexts
    assert new_agent.context_manager.current_context.id == "c1"


def test_restore_state_json_and_invalid_json():
    agent = Agent[str]()
    state = {"contexts": {}, "current_context_id": None}
    json_str = json.dumps(state)

    agent.restore_state_json(json_str, str)

    with pytest.raises(ValueError):
        agent.restore_state_json("[]", str)
