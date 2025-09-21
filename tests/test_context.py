import pytest
from pydantic import BaseModel
from agent_flow.context import Context


class DummyMsg(BaseModel):
    text: str


def test_context_list_behavior():
    ctx = Context[str]()
    ctx.append("hello")
    ctx.append("world")

    assert len(ctx) == 2
    assert ctx[0] == "hello"
    assert ctx[1] == "world"

    ctx[1] = "changed"
    assert ctx[1] == "changed"

    popped = ctx.pop()
    assert popped == "changed"
    assert len(ctx) == 1

    ctx.insert(1, "again")
    assert ctx[1] == "again"

    del ctx[0]
    assert ctx.messages == ["again"]


def test_context_addition_and_iadd():
    ctx = Context[int](messages=[1, 2])
    result = ctx + [3, 4]
    assert result == [1, 2, 3, 4]

    ctx += [5, 6]
    assert ctx.messages == [1, 2, 5, 6]


def test_context_str_and_repr():
    ctx = Context[str](description="test", messages=["a", "b"])
    s = str(ctx)
    r = repr(ctx)
    assert "Context" in s
    assert "test" in s
    assert r == s


def test_context_serialize_messages_various_types():
    ctx = Context(messages=[DummyMsg(text="hi"), "raw", 42, {"a": 1}, [1, 2], True, None])
    serialized = ctx.serialize_messages(ctx.messages)

    assert {"text": "hi"} in serialized
    assert "raw" in serialized
    assert 42 in serialized
    assert {"a": 1} in serialized
    assert [1, 2] in serialized
    assert True in serialized
    assert None in serialized
