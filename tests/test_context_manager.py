import pytest
from agent_flow.context import Context
from agent_flow.context_manager import ContextManager, ContextDict


def test_contextdict_accepts_only_context():
    cd = ContextDict()
    ctx = Context[str]()
    cd["abc"] = ctx
    assert cd["abc"].id == "abc"

    with pytest.raises(ValueError):
        cd["wrong"] = "not a context"


def test_contextmanager_switch_and_remove():
    cm = ContextManager[str]()
    ctx1 = Context[str](id="c1", messages=["msg1"])
    ctx2 = Context[str](id="c2")

    cm.contexts["c1"] = ctx1
    cm.switch_context("c1")
    assert cm.current_context.id == "c1"

    cm.switch_context(ctx2)
    assert "c2" in cm.contexts
    assert cm.current_context.id == "c2"

    cm.remove_context("c2")
    assert "c2" not in cm.contexts
    assert cm.current_context is None


def test_contextmanager_str_and_serialize():
    cm = ContextManager[str]()
    ctx = Context[str](id="c1", messages=["m1"])
    cm.contexts["c1"] = ctx
    cm.switch_context("c1")

    s = str(cm)
    assert "c1" in s

    dump = cm.serialize()
    assert "contexts" in dump
    assert dump["current_context_id"] == "c1"
