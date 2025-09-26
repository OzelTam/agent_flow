from typing import Generic, TypeVar, List, Optional, Any, Type
from pydantic import BaseModel
import uuid, logging

logger = logging.getLogger(__name__)
# Type variables
T = TypeVar('T', bound=Any)       # Message type

# Generic Context
class Context(Generic[T]):
    def __init__(self,id:Optional[str] = None, messages: Optional[List[T]] = None):
        self.id:str = str(id) or str(uuid.uuid4())
        self.messages: List[T] = messages or []
        
    def serialize_messages(self) -> List[Any]:
        serialized = []
        for msg in self.messages:
            if isinstance(msg, BaseModel):
                serialized.append(msg.model_dump())
            elif isinstance(msg, (str, int, float, dict, list, bool, type(None))):
                serialized.append(msg)
            elif hasattr(msg, "__dict__"):
                serialized.append(msg.__dict__)
            else:
                serialized.append(str(msg))
        return serialized
    
    @classmethod
    def restore_messages(cls, messages:list[dict], msg_type:Type[T]) -> List[T]:
        msgs_updated = []
        for msg in messages:
            if not msg or not isinstance(msg, (msg_type, dict)):
                logger.warning(f"Message is neither of type {msg_type} nor dict. Skipping.")
                continue
            if isinstance(msg, msg_type):
                msgs_updated.append(msg)
            elif issubclass(msg_type, BaseModel):
                try:
                    msg_obj = msg_type.model_validate(msg)
                    msgs_updated.append(msg_obj)
                except Exception as e:
                    logger.error(f"Failed to validate message dict to {msg_type}: {e}. Skipping message.")
                    continue
            else:
                try:
                    msg_obj = msg_type(**msg)  # type: ignore
                    msgs_updated.append(msg_obj)
                except Exception as e:
                    logger.error(f"Failed to instantiate {msg_type} from dict: {e}. Skipping message.")
                    continue
            return msgs_updated
                
    def to_dict(self):
        return {
            "id":self.id,
            "messages": self.serialize_messages()
        }
        
    @classmethod
    def from_dict(cls, dict:dict, message_type: Type[T])->"Context[T]":
        id = dict.get("id", None)
        if not id:
            raise ValueError("id field is not found while restoring context")
        msgs = cls.restore_messages(dict.get("messages", []), message_type)
        return Context[T](id=id, messages=msgs)