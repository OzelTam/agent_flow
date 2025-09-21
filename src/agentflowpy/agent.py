import logging
from typing import Generic, TypeVar, Type, Callable, Dict, ParamSpec, Concatenate, Optional
from pydantic import BaseModel, Field, PrivateAttr
from .context import Context
from .context_manager import ContextManager, ContextDict
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)
MessageT = TypeVar("MessageT")
AGENT_START = "agent_start"
AGENT_END = "agent_end"

P = ParamSpec('P')

@dataclass
class StepPass():
    step:str
    kwargs:dict = field(default_factory=dict)
    args:tuple = field(default_factory=tuple)
    refresh_context:bool = field(default=False)

class Agent(BaseModel, Generic[MessageT]):
    context_manager: ContextManager[MessageT] | None = Field(default=None)
    __registered_steps: Dict[str,Callable[Concatenate[Context[MessageT], P], Optional[str | StepPass]]] = PrivateAttr(default_factory=dict)

    
    def model_post_init(self, __context):
        if self.context_manager is None:
            object.__setattr__(self, "context_manager", ContextManager())
            logger.debug("Initialized new ContextManager for Agent.")

    def register_step(self, func: Callable[Concatenate[Context[MessageT], P], Optional[str | StepPass]], tag: str = None):
        if tag is None:
            tag = func.__name__
        if tag in self.__registered_steps:
            logger.exception(f"Attempted to register duplicate step '{tag}'.")
            raise ValueError(f"Step with '{tag}' tag already exists.")
        self.__registered_steps[tag] = func
        logger.debug(f"Registered step '{tag}'.")

    def run(self):
        if self.context_manager is None :
            logger.exception("ContextManager is not set. Cannot run agent.")
            raise ValueError("ContextManager is not set.")
        
        if self.context_manager.current_context is None:
            logger.exception("Current context is not set in ContextManager. Cannot run agent.")
            raise ValueError("Current context is not set in ContextManager.")
        if len(self.__registered_steps.items()) == 0:
            logger.warning("No steps registered. Exiting run().")
            return
        
        step_lead = AGENT_START if AGENT_START in self.__registered_steps else next(iter(self.__registered_steps.keys()))
        logger.debug(f"Starting agent run at step '{step_lead}'.")
        context = self.context_manager.contexts[self.context_manager.current_context.id]
        
        while step_lead != AGENT_END and step_lead is not None:

            step_func: Callable[Concatenate[Context[MessageT], P], Optional[str | StepPass]]
            kwargs = {}
            args = ()
            
            if isinstance(step_lead, StepPass):
                step_name = step_lead.step
                if step_name not in self.__registered_steps and step_name != AGENT_START:
                    logger.exception(f"Step '{step_name}' not registered. Stopping execution.")
                    raise ValueError(f"Step '{step_name}' is not registered.")
                if step_lead.refresh_context:
                    context = self.context_manager.contexts[self.context_manager.current_context.id]
                    logger.debug(f"Context updated to id={context.id} due to StepPass.")
                if not isinstance(step_lead.kwargs, dict):
                    logger.exception("StepPass kwargs must be a dictionary. Stopping execution.")
                    raise TypeError("StepPass kwargs must be a dictionary.")
                if not isinstance(step_lead.args, tuple):
                    logger.exception("StepPass args must be a tuple. Stopping execution.")
                    raise TypeError("StepPass args must be a tuple.")
                    
                kwargs = step_lead.kwargs
                args = step_lead.args
                
                if step_name == AGENT_START:
                    step_func = self.__registered_steps[AGENT_START] if AGENT_START in self.__registered_steps else next(iter(self.__registered_steps.values()))
                else:
                    
                    step_func = self.__registered_steps[step_lead.step]
                logger.debug(f"Executing step '{step_lead.step}':'{step_func.__name__}' with StepPass.")
            elif isinstance(step_lead, str):
                if step_lead not in self.__registered_steps and step_lead != AGENT_START:
                    logger.exception(f"Step '{step_lead}' not registered. Stopping execution.")
                    raise ValueError(f"Step '{step_lead}' is not registered.")
                if step_lead == AGENT_START:
                    step_func = self.__registered_steps[AGENT_START] if AGENT_START in self.__registered_steps else next(iter(self.__registered_steps.values()))
                else:
                    step_func = self.__registered_steps[step_lead]
                logger.debug(f"Executing step '{step_lead}':'{step_func.__name__}'.")
            else:
                logger.exception(f"Invalid step lead type: {type(step_lead)}. Stopping execution.")
                raise TypeError(f"Step lead must be str or StepPass, got {type(step_lead)}.")
            
            step_lead = step_func(context, *args, **kwargs)
            
            
            if step_lead is None:
                logger.debug("Step returned None. Ending run.")
            elif isinstance(step_lead, StepPass):
                logger.debug(f"Step '{step_func.__name__}' returned StepPass to '{step_lead.step}'.")         
            elif isinstance(step_lead, str):
                logger.debug(f"Step '{step_func.__name__}' returned next step '{step_lead}'.")
                
        logger.debug("Agent run completed.")

    def serialize_state(self) -> dict:
        cx = self.context_manager.model_dump() if self.context_manager else {}
        return cx
    
    def serialize_state_json(self, indent: int = 2) -> str:
        cx_json = self.context_manager.model_dump_json(indent=indent) if self.context_manager else "{}"
        return cx_json
    
    def restore_state(self, data: dict, message_type: Type[MessageT]) -> None:
        current_context_id = data.get("current_context_id", None)
        contexts_dict_data = data.get("contexts", {})

        object.__setattr__(self, "context_manager", ContextManager())
        logger.debug("Initialized new ContextManager for Agent during restore_state.")
        contexts_dict = ContextDict()
        for cx_id, cx_data in contexts_dict_data.items():
            cx = _resrore_cx_msg_types(cx_data, message_type)
            contexts_dict[cx_id] = cx
        self.context_manager.contexts = contexts_dict
        self.context_manager.switch_context(current_context_id)
        
        
    def restore_state_json(self, json_str: str, message_type: Type[MessageT]) -> None:
        import json
        data = json.loads(json_str)
        if not isinstance(data, dict):
            logger.exception("JSON string does not represent a dictionary. Cannot restore state.")
            raise ValueError("JSON string does not represent a dictionary.")
        self.restore_state(data, message_type)

def _resrore_cx_msg_types(data:dict, msg_type:Type[MessageT]) -> Context[MessageT]:
    context = Context.model_validate(data)
    msgs_updated = []
    for msg in context.messages:
        if not msg or not isinstance(msg, (msg_type, dict)):
            logger.warning(f"Message in context id={context.id} is neither of type {msg_type} nor dict. Skipping.")
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
                
    context.clear()
    context.extend(msgs_updated)
    return context