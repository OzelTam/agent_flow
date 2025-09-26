from collections.abc import MutableMapping
from typing import Generic, TypeVar, List, Optional, Any, Tuple, Dict, Callable, Concatenate, ParamSpec, Type, Generator, overload
from dataclasses import dataclass, field
from .context import Context
import inspect, logging, asyncio


AGENT_START = "<AGENT_START>"
AGENT_END = "<AGENT_END>"

MessageType = TypeVar('MessageType', bound=Any)
ContextType = TypeVar('ContextType', bound=Context[Any])
P = ParamSpec('P')

logger = logging.getLogger(__name__)

@dataclass
class StepLead:
    step:str
    args:Tuple = field(default_factory=tuple)
    kwargs:dict = field(default_factory=dict)
    modify_flow_context: Optional[ContextType | str] = field(default=None)



class ContextDict(MutableMapping):
    def __init__(self):
        self._store = {}

    # block normal assignment
    def __setitem__(self, key, value):
        raise RuntimeError(
            "Direct assignment with ContextDict()[key] = value is not allowed. "
            "Use `.insert(key, value)` instead."
        )

    # special method to allow controlled insertion
    def insert(self, key, value):
        if not isinstance(value, Context):
            raise ValueError("Passed value must be an instance of Context class/subclass.")
        key = key if key else value.id
        value.id = key
        
        self._store[key] = value

    def __getitem__(self, key):
        return self._store[key]

    def __delitem__(self, key):
        del self._store[key]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._store})"


class Agent(Generic[MessageType, ContextType]):
    
    def __init__(self):
        # Automatically default ContextType to Context[MessageType]
        self.contexts: Dict[str, Context[MessageType]] = ContextDict()  # type: ignore
        self.registered_functions: Dict[str,Callable] = {}
        
        
    def add_contexts(self, contexts:List[ContextType]):
        if not isinstance(contexts, List):
            raise ValueError("You must give List of Contex class/subclass to contexts param.")
        for c in contexts:
            self.add_context(c)
    
    def remove_context(self, context:str | ContextType):
        id = context if isinstance(context, str) else context.id
        del self.contexts[id]
    
    def clear_contexts(self):
        self.contexts = ContextDict()
        
    @overload
    def add_context(self, context: ContextType):...
        
    @overload
    def add_context(self,key:str, context: ContextType):...
    
    def add_context(self, *args, **kwargs) -> None:
        # Handle positional arguments
        if len(args) == 1 and not kwargs:
            context: ContextType = args[0]
            self.contexts.insert(context.id, context)
            logging.debug(f"Context added {context.id}.")
        elif len(args) == 2 and not kwargs:
            key, context = args
            self.contexts.insert(key, context)
            logging.debug(f"Context added {key}.")
        # Handle keyword arguments
        elif "context" in kwargs and "key" not in kwargs and not args:
            context: ContextType = kwargs["context"]
            self.contexts.insert(context.id, context)
            logging.debug(f"Context added {context.id}.")
        elif "context" in kwargs and "key" in kwargs and not args:
            key: str = kwargs["key"]
            context: ContextType = kwargs["context"]
            self.contexts.insert(key, context)
            logging.debug(f"Context added {key}.")
        else:
            raise TypeError(
                "add_context expects (context), (key, context), "
                "or keyword arguments context=..., [key=...]"
            )
    
    def get_context(self, key:str)->ContextType:
        return self.contexts[key]
    
    def register(self, func: Callable[Concatenate[ContextType, P], Optional[str | StepLead]], tag: Optional[str] = None):
        tag = tag if tag else func.__name__
        self.registered_functions[tag] = func
        logging.debug(f"Registered function {func.__name__}:{tag}")
        
    async def _execute_step( self, step_func: Callable, context, *args, **kwargs):
        """Run a step function (sync or async) and return its result."""
        if inspect.iscoroutinefunction(step_func):
            return await step_func(context, *args, **kwargs)
        else:
            return step_func(context, *args, **kwargs)
        
    async def _run_internal( self, context: str | ContextType, entry_point: Optional[str | StepLead] = None):
        """
        Shared logic for running steps (always async).
        Sync wrapper can call this with asyncio.run().
        """

        if len(self.registered_functions) == 0:
            logger.warning("No steps registered. Exiting run().")
            return

        step_lead: str | StepLead

        if entry_point:
            step_lead = entry_point if isinstance(entry_point, StepLead) else StepLead(entry_point)
        else:
            step_lead = AGENT_START if AGENT_START in self.registered_functions else next(iter(self.registered_functions.keys()))

        logger.debug(f"Starting agent run at step '{step_lead}'.")
        cx = self.contexts[context] if isinstance(context, str) else self.contexts[context.id] if isinstance(context, Context) else None
        context = cx if cx else context
        
        if not cx:
            logger.exception(f"Context is not found: {context}")
            raise Exception(f"Context is not found: {context}")
        
        while step_lead != AGENT_END and step_lead is not None:
            step_func: Callable
            args = ()
            kwargs = {}

            if isinstance(step_lead, StepLead):
                step_name = step_lead.step
                if step_name not in self.registered_functions and step_name != AGENT_START:
                    logger.exception(f"Step '{step_name}' not registered. Stopping execution.")
                    raise ValueError(f"Step '{step_name}' is not registered.")
                if step_lead.modify_flow_context:
                    context = self.contexts[step_lead.modify_flow_context] if isinstance(step_lead.modify_flow_context, str) else self.contexts[step_lead.modify_flow_context.id] if issubclass(step_lead.modify_flow_context, Context) else None
                    if not context:
                        logger.exception(f"Context is not found: {context}")
                        raise Exception(f"Context is not found: {context}")
                    logger.debug(f"Context updated to id={context.id} due to StepLead.")
                if not isinstance(step_lead.kwargs, dict):
                    raise TypeError("StepLead kwargs must be a dictionary.")
                if not isinstance(step_lead.args, tuple):
                    raise TypeError("StepLead args must be a tuple.")

                kwargs = step_lead.kwargs
                args = step_lead.args

                if step_name == AGENT_START:
                    step_func = self.registered_functions[AGENT_START] if AGENT_START in self.registered_functions else next(iter(self.registered_functions.values()))
                else:
                    step_func = self.registered_functions[step_lead.step]
                logger.debug(f"Executing step '{step_lead.step}':'{step_func.__name__}' with StepLead.")
            elif isinstance(step_lead, str):
                if step_lead not in self.registered_functions and step_lead != AGENT_START:
                    raise ValueError(f"Step '{step_lead}' is not registered.")
                if step_lead == AGENT_START:
                    step_func = self.registered_functions[AGENT_START] if AGENT_START in self.registered_functions else next(iter(self.registered_functions.values()))
                else:
                    step_func = self.registered_functions[step_lead]
                logger.debug(f"Executing step '{step_lead}':'{step_func.__name__}'.")
            else:
                raise TypeError(f"Step lead must be str or StepLead, got {type(step_lead)}.")

            step_lead = await self._execute_step(step_func, context, *args, **kwargs)

            if step_lead is None:
                logger.debug("Step returned None. Ending run.")
            elif isinstance(step_lead, StepLead):
                logger.debug(f"Step '{step_func.__name__}' returned StepLead to '{step_lead.step}'.")         
            elif isinstance(step_lead, str):
                logger.debug(f"Step '{step_func.__name__}' returned next step '{step_lead}'.")

        logger.debug("Agent run completed.")
    
    def run(self, context: str | ContextType, entry_point: Optional[str | StepLead] = None):
            """Sync version of run."""
            return asyncio.run(self._run_internal(context, entry_point))
    
    async def arun(self, context: str | ContextType, entry_point: Optional[str | StepLead] = None):
        """Async version of run."""
        return await self._run_internal(context, entry_point)
    
    def contexts_to_dicts(self)->List[Dict]:
        contexts = []
        for c in self.contexts.values():
            contexts.append(c.to_dict())
        return contexts
        
    @classmethod
    def contexts_from_dicts(cls, cx_dicts: List[dict],
                         msg_type: Optional[Type[MessageType]] = None, 
                         cx_type: Optional[Type[ContextType]] = None)->List[ContextType]:
        msg_type = msg_type if msg_type else dict
        cx_type = cx_type if cx_type else Context[Any]
        res:List[ContextType] = []
        for dct in cx_dicts:
             res.append(cx_type.from_dict(dct, msg_type))
        return res

class SimpleAgent(Agent[MessageType, Context[MessageType]]):
    pass
