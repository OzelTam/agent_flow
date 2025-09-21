from typing import Dict, Generic, Optional, Type, Union, Any
from pydantic import BaseModel, Field, PrivateAttr, model_serializer, field_validator, model_validator
from .context import Context, MessageT
import logging

logger = logging.getLogger(__name__)

class ContextDict(Dict[str, Context[MessageT]]):
    def __setitem__(self, key, value):
        if not isinstance(value, Context) and not issubclass(type(value), Context):
            logger.exception(f"Attempted to set non-Context value in ContextManager: {type(value)}")
            raise ValueError("Value must be an instance of Context or its subclass.")
        value.id = key  # Ensure the context's id matches the key
        logger.debug(f"Setting context with id={key} in ContextManager.")
        return super().__setitem__(key, value)
    
    def __delitem__(self, key):
        logger.debug(f"Deleting context with id={key} from ContextManager.")
        return super().__delitem__(key)
    

class ContextManager(BaseModel, Generic[MessageT]):
    context_type: Type[Context[MessageT]] = Field(default=Context)
    contexts: ContextDict = Field(default_factory=ContextDict)
    _current_context: Optional[Context[MessageT]] = PrivateAttr(default=None)
    model_config = {"arbitrary_types_allowed": True,}
    
    @property
    def current_context(self) -> Optional[Context[MessageT]]:
        return self._current_context
    
    @current_context.setter
    def current_context(self, value: Optional[Context[MessageT]]) -> None:
        if value is not None and not isinstance(value, Context):
            logger.exception("current_context must be a Context instance or None.")
            raise ValueError("current_context must be a Context instance or None.")
        self.switch_context(value)
        
    # Main Methods
                
    def switch_context(self, value: Union[str, Context[MessageT], None]) -> None:
        if value is None:
            logger.debug("Switching to None (clearing current_context).")
            self._current_context = None
            return

        if isinstance(value, str):
            if value not in self.contexts:
                logger.exception(f"No context found with id '{value}'.")
                raise KeyError(f"No context found with id '{value}'")
            self._current_context = self.contexts[value]
            logger.debug(f"Switched to context id={value}.")
        elif isinstance(value, Context):
            if value.id not in self.contexts:
                self.contexts[value.id] = value
                logger.debug(f"Added new context id={value.id}.")
            self._current_context = self.contexts[value.id]
            logger.debug(f"Switched to context id={value.id}.")

    def remove_context(self, value: Union[str, Context[MessageT]]) -> None:
        context_id = value.id if isinstance(value, Context) else value
        context_id = str(context_id)

        if context_id in self.contexts:
            cx =  self.contexts[context_id]
            cc_id = str(self._current_context.id)
            if cx.id == cc_id:
                self._current_context = None
                logger.debug(f"Current context id={cc_id} removed, setting current_context to None.")
            del self.contexts[context_id]
            logger.debug(f"Removed context id={cx.id}:{cc_id}.")
        else:
            logger.warning(f"Attempted to remove non-existent context id={context_id}.")
            

    # Utils
    def __str__(self) -> str:
        return f"ContextManager(current_context_id={self._current_context.id if self._current_context else None}, contexts={[c for c in self.contexts.values()]})"

    def __repr__(self) -> str:
        return self.__str__()

    # Serializer
    @model_serializer
    def serialize(self) -> dict[str, Any]:
        return {
            "contexts": {k: v.model_dump() for k, v in self.contexts.items()},
            "current_context_id": self._current_context.id if self._current_context else None,
        }