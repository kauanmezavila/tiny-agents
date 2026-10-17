<div align="center">
  <table bgcolor="#ffffff">
    <tr><td><img src="imgs/logo.png" alt="Tiny Agents" width="180" /></td></tr>
  </table>
  <h1>Tiny Agents</h1>
  <p>Small building blocks for Python agents and harnesses.</p>
  <p><b>v0.2.3: multiple providers, less configuration, less code, more action.</b></p>
</div>

Tiny Agents is a framework for building custom agent harnesses. Version 0.2.3 adds `AgentHarness`, which connects model/provider selection, clients, tools, conversation context, and panel callbacks. Application configuration and harness creation stay in `main.py`; reusable wiring lives in the framework. The framework also includes async command execution, OpenAI-compatible provider clients, JSON-based tool calling, in-memory conversation context, and terminal formatting utilities.

The core works independently of the panel. Applications connect tools to the interface through callbacks, so the same tools can also run in a regular terminal.

For step-by-step examples, see the [usage guide](docs/USAGE.md). The guide covers direct model calls, adding tools, context management, provider setup, and assembling the panel harness.

## Function organization

| Module                | Main responsibilities                                                                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------ |
| `src/tinyAgents.py`   | `startClient`, model request functions, tool loading and execution, context storage and compaction.          |
| `src/AgentHarness.py` | `AgentHarness`: connects provider/model state, tools, requests, context, worker, and panel callbacks.        |
| `src/Panel/Panel.py`  | `initPanel`, `Command`, `PanelContext`, `AsyncWorker`, command dispatch, and terminal UI.                    |
| `Tools/`              | Tool schemas, handler mappings, and tool implementations such as `hourNow` and shell commands.               |
| `Packages/`           | Presentation helpers such as `prettyResolve` and terminal colors.                                            |
| `main.py`             | Application configuration and assembly: profiles, prompt, tool setup, commands, panel settings, and startup. |

Keep application-specific behavior and configuration in `main.py` or app modules. Reusable request and wiring behavior belongs in the framework modules; tool implementations belong in `Tools/`.

## Providers and models

| Provider     | Models                                                                          |
| ------------ | ------------------------------------------------------------------------------- |
| NVIDIA NIM   | `openai/gpt-oss-20b`, `nvidia/nemotron-3-super-120b-a12b`, `z-ai/glm-5-3-flash` |
| Cloud Ollama | `gpt-oss:20b`                                                                   |

## Installation

The core requires Python 3.9 or newer. The panel example requires Python 3.10 or newer because its handler annotations use union types.

From a repository checkout, install the core and the example's additional dependencies:

```bash
uv sync
uv pip install prompt-toolkit python-dotenv
```

Or use pip:

```bash
python -m pip install .
python -m pip install prompt-toolkit python-dotenv
```

The panel and example tools currently run from the checkout: the package configuration includes `src` and `Packages`, but does not include `src.Panel` or `Tools`. `prompt-toolkit` and `python-dotenv` are not declared core dependencies.

Create a `.env` file in the project root:

```dotenv
API_KEY_NVIDIA=your-nvidia-api-key
API_KEY_OLLAMA=your-ollama-api-key
```

The example reads provider keys from these environment variables. Configure available providers and model IDs in `profiles` in `main.py`. `startClient` uses the NVIDIA and Cloud Ollama endpoints for those known providers; other providers can provide `baseUrl` in their profile. Use models that support function tool calling when enabling tools.

## Panel example

The repository's `main.py` is the runnable panel example. Keep application-specific settings there, then create an `AgentHarness` to connect them to the framework:

```python
import os
from dotenv import load_dotenv
from prompt_toolkit.patch_stdout import patch_stdout

from src.tinyAgents import *
from src.AgentHarness import AgentHarness
from src.Panel.Panel import initPanel, PanelContext, Command, AsyncWorker
from Packages.colors import *

agent_worker = AsyncWorker()
load_dotenv()

profiles = {
    "nvidia": {
        "models": ["openai/gpt-oss-20b", "nvidia/nemotron-3-super-120b-a12b"],
        "apiKey": os.getenv("API_KEY_NVIDIA"),
    },
    "cloud-ollama": {
        "models": ["gpt-oss:20b"],
        "apiKey": os.getenv("API_KEY_OLLAMA"),
    },
    # For an unmapped provider, supply its OpenAI-compatible URL:
    # "my-provider": {"models": ["model-id"], "apiKey": "...",
    #                  "baseUrl": "https://api.example.com/v1"},
}
selected = ["nvidia", "nvidia/nemotron-3-super-120b-a12b"]
tools = loadTools("Tools/tools.json")
tool_handlers = loadToolHandlers("Tools/toolsCall.json")
agent = AgentHarness(
    profiles=profiles,
    selected=selected,
    tools=tools,
    tool_handlers=tool_handlers,
    pre_prompt="You are a helpful assistant. Use tools when asked.",
    worker=agent_worker,
)


def echo(args: list[str], ctx: PanelContext) -> str:
    return " ".join(args)


def clear_command(args: list[str], ctx: PanelContext) -> None:
    ctx.clear()


def exit_command(args: list[str], ctx: PanelContext) -> None:
    ctx.exit()


COMMANDS = [
    Command("/echo", "Repeat the arguments", echo),
    Command("/clear", "Clear the panel", clear_command),
    Command("/exit", "Exit the panel", exit_command),
    Command("/compact", "Compact the context window", agent.compact_context),
]

PANEL_CONFS = {
    "NAME_TEXT": f"{BOLD + BLUE}KML CODE{RESET}",
    "SUBNAME_TEXT": f"{ITALIC}The Tiny Agents Ultimate Framework{RESET}",
    "INPUT_BOX_UPPER_TEXT": f"{DIM}Try typing something{RESET}",
    "THINKING_TEXT": "Thinking...",
    "MODEL_NAME": agent.model,
    "MODEL_PROVIDER": agent.provider,
    "MODEL_OPTION": agent.model_option,
    "CONTEXT_WINDOW_SIZE": contextWindowSize,
    "CONTEXT_WINDOW_MAX": 10000,
    "THEME": "default",
    "MESSAGE_SPACING": 1,
    "STYLE": {
        "title": BOLD + BLUE,
        "user": BG_BLUE + WHITE,
        "model": WHITE,
        "error": RED,
        "separator": DIM + BLACK,
        "hint": DIM,
        "input-field": BG_BLUE + WHITE,
        "completion-menu": WHITE,
        "completion-menu.completion": WHITE,
        "completion-menu.completion.current": BG_BLUE + BOLD + BLUE,
        "scrollbar": BG_BLACK,
        "scrollbar.button": BG_BLACK + WHITE,
    },
    "COMMANDS": COMMANDS,
    "COMMANDS_LIST": [command.name for command in COMMANDS],
    "MODEL_HANDLER": agent.model_handler,
    "MODEL_OPTIONS": agent.model_options(),
    "MODEL_OPTION_LABELS": agent.model_option_labels(),
    "MODEL_SELECT_HANDLER": agent.select_model,
}

panel = initPanel(PANEL_CONFS)

with patch_stdout():
    panel.run()

```

Run the example from the project root so the tool configuration files and Python modules can be found:

```bash
uv run --with prompt-toolkit --with python-dotenv main.py
```

Or, after installing the dependencies with pip:

```bash
python main.py
```

`AgentHarness` runs model requests and tool execution through the supplied `AsyncWorker`, saves each exchange to the shared context, and connects tools that accept a `write` callback to the panel. `main.py` remains responsible for configuration, application-specific commands, and creating the harness.

Commands include `/echo`, `/clear`, `/exit`, `/compact`, and `/model`. Run `/model` to open the selector above the input box, move with ↑/↓, choose with Enter, or close it with Esc. The options show `provider / model`; direct selection accepts an option number or its `provider::model` ID. The harness recreates the client when the provider changes and uses that provider's configured key and URL. For a new provider, add its models and key in `profiles` and set `baseUrl` there.

`/compact` uses the currently selected client and model. `/clear` clears the visible chat, not the framework's conversation context. Scroll with PgUp/PgDn, or jump to the beginning and end with Ctrl+Home/Ctrl+End.

## Panel configuration

Pass a dictionary to `initPanel` from `src.Panel.Panel`:

| Key                         | Purpose                                                                                                                          |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `NAME_TEXT`, `SUBNAME_TEXT` | Title and subtitle; ANSI formatting is supported.                                                                                |
| `INPUT_BOX_UPPER_TEXT`      | Extra text beside the scrolling hints.                                                                                           |
| `THINKING_TEXT`             | Activity label; defaults to `Thinking...`.                                                                                       |
| `MODEL_NAME`                | Current model name displayed in the panel; updated after selection.                                                              |
| `MODEL_PROVIDER`            | Current provider displayed with the model when set.                                                                              |
| `MODEL_OPTION`              | Current selector ID, usually `provider::model`, used to highlight the selected option.                                           |
| `MODEL_OPTIONS`             | Optional list of model IDs that enables the `/model` selector.                                                                   |
| `MODEL_OPTION_LABELS`       | Optional mapping from selector IDs to human-readable labels.                                                                     |
| `MODEL_SELECT_HANDLER`      | Optional callback receiving the selected option ID.                                                                              |
| `MODEL_HANDLER`             | Callable receiving `(text, ctx)` and returning a response or `None`; synchronous and async handlers are supported.               |
| `COMMANDS`                  | List of `Command(name, description, handler)` instances. Command handlers receive `(args, ctx)` and may be synchronous or async. |
| `COMMANDS_LIST`             | Completion suggestions; defaults to registered command names.                                                                    |
| `CONTEXT_WINDOW_SIZE`       | Function taking no arguments and returning the current usage; defaults to zero.                                                  |
| `CONTEXT_WINDOW_MAX`        | Positive integer used as the meter's maximum; defaults to `10000`.                                                               |
| `THEME`                     | `default`, `dark`, `light`, or `ocean`; defaults to `default`.                                                                   |
| `MESSAGE_SPACING`           | Number of blank lines between messages; defaults to `1`, and accepts `0`.                                                        |
| `STYLE`                     | Style overrides for the selected theme.                                                                                          |

`PanelContext` exposes `write(text)`, `clear()`, and `exit()`. Writes from the agent worker are scheduled on the UI loop and chat updates are batched during bursts of output. The spinner refreshes only during activity, and unchanged ANSI lines are cached.

Command handlers are awaited when async; synchronous handlers run in a thread. Async commands are prevented from starting during a model request or another async command. `/clear` and `/exit` remain available. Async handlers that use the synchronous SDK must delegate that work to `AsyncWorker`, as `/compact` does in the example. `dispatch` is now async and direct callers must await it.

The activity line stays reserved above the hints. The spinner and activity text appear only while the model handler is running; the context meter remains visible. Its color changes at 70% and 90% usage, and the bar fills completely at or above the maximum.

The size callback and maximum must use the same unit. `contextWindowSize` counts saved user and response characters, not model tokens, tool logs, or the full API request. The meter updates when the saved context changes. Its maximum is visual configuration: it does not enforce a limit or compact context automatically.

### Themes and message styles

Explicit `STYLE` values override the selected theme. To use a complete preset, omit the corresponding overrides from the example:

```python
PANEL_STYLE = {
    "THEME": "ocean",
    "MESSAGE_SPACING": 1,
    "STYLE": {
        "user": "bg:#173f50 #ffffff",
        "model": "#daf4f4",
        "error": "#ff6b6b bold",
        "context-low": "#4caf80",
        "context-warning": "#e9b949",
        "context-full": "#ef6461 bold",
    },
}
```

Styles accept prompt_toolkit style strings or ANSI constants such as `BG_BLUE + WHITE`. `user` applies to sent messages, `model` to returned model responses, and `error` to messages beginning with `[ERROR]`. Tool output remains independent. ANSI formatting embedded in messages is preserved and can override their text color.

The model selector appears directly above the input box and uses the `completion-menu` background style. Its choices use `radio` and `radio-checked` styles. Other style keys include `chat-area`, `hint`, `separator`, `input-field`, `completion-menu.completion`, `completion-menu.completion.current`, `scrollbar`, and `scrollbar.button`.

## Tool calling

`Tools/tools.json` defines the function schemas offered to the model. `Tools/toolsCall.json` maps their names to Python handlers:

```json
{
  "hourNow": "Tools.hourNow.hourNow:hourNow",
  "runInShell": "Tools.runInShell.runInShell:runInShell",
  "runInShellCool": "Tools.runInShell.runInShell:runInShellCool"
}
```

The included tools are examples and conveniences for applications:

| Tool                               | Behavior                                                                                             |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `hourNow()`                        | Returns the current UTC date and time under `utc`.                                                   |
| `runInShell(cmd)`                  | Collects shell output without displaying it.                                                         |
| `runInShellCool(cmd, write=print)` | Collects shell output and sends the command, output lines, and exit status to the supplied callback. |

Both shell tools return `logs` and `exitCode`, combining standard output and standard error. Output is read by line, so subprocess buffering can delay updates. Shell commands execute locally with `shell=True`.

To add a tool, implement an importable function, add its schema to `tools.json`, and map its name to `module:function` in `toolsCall.json`. Handler keyword arguments must match the schema's parameter names. Handler mappings import Python modules and should come from trusted configuration.

`messageToLLMTools` lets the model choose tools, executes their handlers, sends results back to the model, and returns `(completion, executedTools)`. It allows up to five rounds of tool execution and raises `RuntimeError("Tool call limit exceeded")` if more calls are still requested.

Each execution record includes `id`, `name`, `arguments`, and `ok`, with `result` on success or `error` on failure. Unknown tools, invalid arguments, and handler exceptions become failed tool results. Configuration loading and API errors propagate to the caller.

### Tools without the panel

Tools do not import the panel. The output callback is supplied by the application and is not a model parameter or part of the JSON schema:

```python
from Tools.runInShell.runInShell import runInShellCool

result = runInShellCool("echo hello")
```

`AgentHarness` connects tools that accept a `write` parameter to the panel's `ctx.write` callback when handling a request.

## Core without the panel

Import the core from `src.tinyAgents` and the panel separately from `src.Panel.Panel`. The request helpers are async functions and must be awaited:

```python
import asyncio
import os

from src.tinyAgents import startClient, messageToLLM, addToContextWindow

async def run():
    model = "nvidia/nemotron-3-super-120b-a12b"
    profiles = {"nvidia": {"apiKey": os.environ["API_KEY_NVIDIA"]}}
    client = startClient(profiles, ["nvidia", model])
    message = "Hello"
    completion = await messageToLLM(
        client, model, "You are a helpful assistant.", message
    )
    response = completion.choices[0].message.content or ""
    addToContextWindow(message, response, "user input")
    print(response)

asyncio.run(run())
```

This example reads environment variables directly. The helpers retain synchronous SDK calls internally, so applications with an interactive event loop should run them in a worker, as the panel example does.

## Context and API

| API                                                                          | Purpose                                                                                |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `startClient(profiles, selected)`                                            | Create an OpenAI-compatible client using the selected provider's key and URL.          |
| `messageToLLM(client, model, prePrompt, message)`                            | Async request without tool calling; returns the SDK completion.                        |
| `loadTools(path)`                                                            | Load the `tools` array from JSON.                                                      |
| `loadToolHandlers(path)`                                                     | Import and validate configured Python handlers.                                        |
| `messageToLLMTools(client, model, prePrompt, message, TOOLS, TOOL_HANDLERS)` | Async request with tool execution; returns completion and execution records.           |
| `addToContextWindow(message, response, objectType, toolsRunned=[])`          | Save an exchange and optional tool records.                                            |
| `contextWindow`                                                              | Shared in-memory conversation dictionary.                                              |
| `contextWindowSize()`                                                        | Count saved user and response tokens.                                                  |
| `clearContextWindow()`                                                       | Clear the saved conversation.                                                          |
| `OldCompactContextWindow(maxSize)`                                           | Remove the oldest exchanges until the size is within a non-negative character limit.   |
| `NewCompactContextWindow(client, model)`                                     | Async request for a summary that replaces the saved conversation; must be awaited.     |
| `prettyResolve(text)`                                                        | Format Markdown headings and emphasis for terminal output.                             |
| `AgentHarness(...)`                                                          | Connect provider/model selection, tool handlers, context, worker, and panel callbacks. |

Requests do not automatically save their results. Pass `executedTools` to `addToContextWindow` to retain tool records alongside an exchange. Context is shared within the process and is lost when it exits. Model-based compaction makes an additional API request and may lose details.

Compaction follows the same async calling pattern as `messageToLLM`:

```python
await NewCompactContextWindow(client, model)
```

From the panel's UI loop, use the existing worker to keep the synchronous SDK request off the UI thread:

```python
await agent_worker.run(NewCompactContextWindow(client, model))
```

## Project status

Version 0.2.3 adds the reusable `AgentHarness` and provider-aware model switching. The framework remains under active development. See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Contributing

Suggestions and contributions are welcome. Open an issue or submit a pull request with a clear description of the change.

## Ownership

Developed under [KML Research Labs](https://github.com/KML-Research-Labs) by [Kauan Mezavila](https://github.com/kauanmezavila).

## License

Released under the [MIT License](LICENSE).
