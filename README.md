# AgentFlowPy

**AgentFlowPy** is a lightweight Python framework for building workflows with flexible & extensible context management. It allows developers to create agents that execute sequences of steps, maintain context, implement custom contexts, pass arguments between steps, and support typed messages.

## Features

- Step-based workflow execution.
- Flexible **context management** with multiple contexts.
- Pass arguments between steps using `StepLead`.
- Typed messages with simple types, `Pydantic`, `dtaclasses` and raw class support.
- Easy integration of custom logic in each step.
- Looping and conditional flow control (`AGENT_START`, `AGENT_END`, `StepLead`).

## Installation

```bash
pip install agentflowpy
```

## Examples
- **Basic Usage :** [basic_flow.py](./examples/basic_flow.py) *Sample of basic use.*
- **Typed Message :** [typed_message.py](./examples/typed_message.py) *Typed Message and Conditional flow.*
- **Custom Context Implementation:** [custom_context.py](./examples/custom_context.py) *Create/Manage custom context types*
- **Pass Arguments :** [pass_args.py](./examples/pass_args.py) *Passing additional arguments to next step.*
- **Context Switch In Flow :** [mid_switch.py](./examples/mid_switch.py) *Switch context while in flow to effect next steps.*
- **Serialize/Restore Contexts:** [save_load_state.py](./examples/save_load_state.py) *Serialize and Restore context_manager state*
