# Tiny Agents usage guide

This guide shows how to use Tiny Agents without the panel, add tools, and connect an agent to the terminal panel through `AgentHarness`.

Install the distribution as `by-tiny-agents`; import it in Python as `tinyAgents`.

## Where each responsibility belongs

| Location | Responsibility |
| --- | --- |
| `tinyAgents/` | Public import interface: package-level exports plus `core`, `harness`, `panel`, `colors`, and `formatting` modules. |
| `main.py` | Application configuration and assembly: provider profiles, selected model, tools, system instructions, panel commands, and startup. |
| `src/AgentHarness.py` | Reusable wiring between providers, model selection, tool calls, conversation context, the worker, and panel callbacks. |
| `src/tinyAgents.py` | Framework primitives: API clients and requests, JSON tool loading/execution, conversation context, and compaction. |
| `src/Panel/` | Terminal UI, command dispatch, worker, themes, and `PanelContext`. |
| `Tools/` | Packaged tool schemas, handler mappings, and tool implementations. |
| `Packages/` | Small presentation helpers such as terminal colors and Markdown formatting. |

Put behavior that is specific to an application in its own module or in `Tools/`. Keep reusable framework behavior in `src/` and expose it through `tinyAgents/`. `main.py` selects and connects those pieces; it should not need to implement the model request and tool execution flow itself.

## Install and configure

Install the project and the panel example's additional dependencies:

```bash
uv sync --extra panel
```

With pip, install from a checkout using `python -m pip install ".[panel]"`. To install from GitHub, use `python -m pip install "by-tiny-agents[panel] @ git+https://github.com/kauanmezavila/tiny-agents.git"`. The package provides the core, harness, panel, tools, schemas, and helper modules. `main.py` remains the repository's runnable example.

Create a `.env` file in the project root with the keys needed by the providers you enable:

```dotenv
API_KEY_NVIDIA=your-nvidia-api-key
API_KEY_OLLAMA=your-ollama-api-key
```

The provider profile maps a provider name to its key and available models. NVIDIA and Cloud Ollama use URLs defined in `startClient`. For another OpenAI-compatible provider, supply `baseUrl`:

```python
profiles = {
    "nvidia": {
        "models": ["nvidia/nemotron-3-super-120b-a12b"],
        "apiKey": os.getenv("API_KEY_NVIDIA"),
    },
    "my-provider": {
        "models": ["my-model"],
        "apiKey": os.getenv("MY_PROVIDER_API_KEY"),
        "baseUrl": "https://api.example.com/v1",
    },
}
selected = ["nvidia", "nvidia/nemotron-3-super-120b-a12b"]
```

Each model ID must be accepted by the selected provider. When selecting a model from another provider, `AgentHarness` creates a client with that provider's key and URL.

## Make a request without the panel

The core request helpers can be used directly in a script. The SDK calls are synchronous internally, even though these helpers are `async`:

```python
import asyncio
import os

from tinyAgents import addToContextWindow, messageToLLM, startClient

model = "nvidia/nemotron-3-super-120b-a12b"
profiles = {"nvidia": {"apiKey": os.environ["API_KEY_NVIDIA"]}}
client = startClient(profiles, ["nvidia", model])


async def main():
    prompt = "Hello"
    completion = await messageToLLM(
        client,
        model,
        "You are a helpful assistant.",
        prompt,
    )
    response = completion.choices[0].message.content or ""
    addToContextWindow(prompt, response, "user input")
    print(response)


asyncio.run(main())
```

`messageToLLM` returns the provider SDK completion. This helper includes the shared context in the request, but saving the new exchange is the caller's responsibility. `addToContextWindow` stores it in process memory; it is lost when the program exits.

## Add and load a tool

A tool has three parts: a Python implementation, a JSON schema offered to the model, and a mapping from the schema name to the Python function.

For example, implement a tool in `Tools/example.py`:

```python
def greet(name: str) -> dict:
    return {"message": f"Hello, {name}!"}
```

Add its schema to `Tools/tools.json`:

```json
{
  "type": "function",
  "function": {
    "name": "greet",
    "description": "Greet a person by name.",
    "parameters": {
      "type": "object",
      "properties": {"name": {"type": "string"}},
      "required": ["name"],
      "additionalProperties": false
    }
  }
}
```

Add the handler mapping to `Tools/toolsCall.json`:

```json
{
  "greet": "Tools.example:greet"
}
```

The project example has other mappings in that file, so add this property without removing them. Load both files in the application setup:

```python
tools = loadTools("Tools/tools.json")
tool_handlers = loadToolHandlers("Tools/toolsCall.json")
```

The packaged JSON files can be loaded by these same paths after installation; the framework falls back to package resources when the files are not in the current directory.

`messageToLLMTools` offers the schemas to the model, checks that requested handlers are allowed, passes decoded JSON arguments to them, and sends their results back to the model. It allows up to five tool-call rounds per request.

## Assemble the panel harness

Create the worker and harness in the application setup. The harness owns the reusable request flow; the app supplies its configuration:

```python
from tinyAgents import AgentHarness
from tinyAgents.panel import AsyncWorker, Command, initPanel

worker = AsyncWorker()
agent = AgentHarness(
    profiles=profiles,
    selected=selected,
    tools=tools,
    tool_handlers=tool_handlers,
    pre_prompt="You are a helpful assistant. Use tools when asked.",
    worker=worker,
)
```

Pass the harness callbacks and selector data to `initPanel`:

```python
PANEL_CONFS = {
    "MODEL_NAME": agent.model,
    "MODEL_PROVIDER": agent.provider,
    "MODEL_OPTION": agent.model_option,
    "MODEL_HANDLER": agent.model_handler,
    "MODEL_OPTIONS": agent.model_options(),
    "MODEL_OPTION_LABELS": agent.model_option_labels(),
    "MODEL_SELECT_HANDLER": agent.select_model,
    "CONTEXT_WINDOW_SIZE": contextWindowSize,
    "COMMANDS": [
        Command("/compact", "Compact the context", agent.compact_context),
        # Add app-specific commands here.
    ],
}

panel = initPanel(PANEL_CONFS)
panel.run()
```

The selector displays `provider / model`; each option ID is `provider::model`. When the provider changes, the harness replaces its client. It also captures the client and model together for each request. For tools whose handler accepts a `write` argument, the harness supplies the panel's `ctx.write` callback so output appears in the chat.

`AsyncWorker` keeps synchronous SDK work off the panel's UI loop. Use `agent.compact_context` for `/compact` so compaction uses the current provider and model too.

## Context helpers

The framework exposes a shared in-memory `contextWindow` and these helpers:

```python
from tinyAgents import (
    addToContextWindow,
    clearContextWindow,
    contextWindow,
    contextWindowSize,
    NewCompactContextWindow,
)

addToContextWindow("question", "answer", "user input")
print(contextWindowSize())

async def compact(client, model):
    await NewCompactContextWindow(client, model)

clearContextWindow()
```

`NewCompactContextWindow` asks the selected model for a summary and replaces the current context with it. Call it from an async function and, in panel code, run it through `AsyncWorker` (or use `agent.compact_context`).

## Run the repository example

From the repository root:

```bash
uv run --with prompt-toolkit --with python-dotenv main.py
```

The example's provider list, system prompt, tools, commands, and visual panel settings are configured in `main.py`. The generic request, selection, tool, and context wiring is provided by the framework.
