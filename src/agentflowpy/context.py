from typing import Any, Generic, Iterator, List, Optional, TypeVar, Union, overload
from collections.abc import MutableSequence
from pydantic import BaseModel, Field, field_serializer
import uuid, logging

logger = logging.getLogger(__name__)
MessageT = TypeVar("MessageT")



class Context(BaseModel, Generic[MessageT], MutableSequence[MessageT]):
    description: Optional[str] = Field(default=None)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[MessageT] = Field(default_factory=list)
    model_config = {"arbitrary_types_allowed": True}

    #  List operations
    @overload
    def __getitem__(self, index: int) -> MessageT: ...
    @overload
    def __getitem__(self, index: slice) -> List[MessageT]: ...

    def __getitem__(self, index: Union[int, slice]) -> Union[MessageT, List[MessageT]]:
        return self.messages[index]

    def __setitem__(self, index: Union[int, slice], value: Union[MessageT, List[MessageT]]) -> None:
        self.messages[index] = value
        logger.debug(f"Set item(s) at {index} in Context(id={self.id}).")

    def __delitem__(self, index: Union[int, slice]) -> None:
        del self.messages[index]
        logger.debug(f"Deleted item(s) at {index} in Context(id={self.id}).")

    def __len__(self) -> int:
        return len(self.messages)

    def insert(self, index: int, value: MessageT) -> None:
        self.messages.insert(index, value)
        logger.debug(f"Inserted item at index {index} in Context(id={self.id}).")

    def pop(self, index: int = -1) -> MessageT:
        msg = self.messages.pop(index)
        logger.debug(f"Popped message from Context(id={self.id}).")
        return msg

    def __iter__(self) -> Iterator[MessageT]:
        return iter(self.messages)

    def __add__(self, other: List[MessageT]) -> List[MessageT]:
        if not isinstance(other, list):
            raise TypeError("Operand must be a list")
        return self.messages + other

    def __iadd__(self, other: List[MessageT]) -> "Context[MessageT]":
        if not isinstance(other, list):
            raise TypeError("Operand must be a list")
        self.messages += other
        logger.debug(f"Extended Context(id={self.id}) with {len(other)} items.")
        return self

    def __str__(self) -> str:
        return f"Context(id={self.id}, description={self.description!r}, messages={len(self.messages)})"

    def __repr__(self) -> str:
        return self.__str__()

    @field_serializer("messages")
    def serialize_messages(self, messages: List[MessageT]) -> List[Any]:
        serialized = []
        for msg in messages:
            if isinstance(msg, BaseModel):
                serialized.append(msg.model_dump())
            elif isinstance(msg, (str, int, float, dict, list, bool, type(None))):
                serialized.append(msg)
            elif hasattr(msg, "__dict__"):
                serialized.append(msg.__dict__)
            else:
                serialized.append(str(msg))
        return serialized

 