<div align="center">
  <table bgcolor="#ffffff">
    <tr><td><img src="imgs/logo.png" alt="Tiny Agents" width="180" /></td></tr>
  </table>
  <h1>Tiny Agents</h1>
  <p>Small building blocks for Python agents and harnesses.</p>
</div>

Tiny Agents is a framework for building custom agent harnesses. Version 0.2.2 adds an interactive model selector to the terminal panel, restores normal command completion while the selector is closed, and keeps the displayed model synchronized with the selection. It also includes async command execution, the NVIDIA API client, in-memory conversation context, JSON-based tool calling, and terminal formatting utilities.

The core works independently of the panel. Applications connect tools to the interface through callbacks, so the same tools can also run in a regular terminal.

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
API_KEY=your-api-key
MODEL=your-model-id
```

Use a model that supports function tool calling. The client uses NVIDIA's OpenAI-compatible endpoint at `https://integrate.api.nvidia.com/v1`.

## Panel example

The following is the current `main.py` example. Save it as `main.py` in the project root if it is not present in your checkout; that filename is ignored by Git.

```python
import os
from functools import partial
from dotenv import load_dotenv
from prompt_toolkit.patch_stdout import patch_stdout

from src.tinyAgents import *
from src.Panel.Panel import initPanel, PanelContext, Command, AsyncWorker
from Packages.prettyResolver import prettyResolve
from Packages.colors import *

agent_worker = AsyncWorker()

load_dotenv()

apiKey = os.getenv("API_KEY")
model = os.getenv("MODEL")

client = startClient(apiKey)

toolsJsonPath = os.path.join("Tools", "tools.json")
toolsCallJsonPath = os.path.join("Tools", "toolsCall.json")

TOOLS = loadTools(toolsJsonPath)
TOOLS_HANDLERS = loadToolHandlers(toolsCallJsonPath)

prePrompt = "You are a helpful agent that provides detailed answers. Use tools only when the user asks."


async def compactContext(args: list[str], ctx: PanelContext) -> None:
    await agent_worker.run(NewCompactContextWindow(client, model))


def echo(args: list[str], ctx: PanelContext) -> str:
    return " ".join(args)


def clear_command(args: list[str], ctx: PanelContext) -> None:
    ctx.clear()


def exit_command(args: list[str], ctx: PanelContext) -> None:
    ctx.exit()


async def _process_agent(prompt: str, tool_handlers):
    completion, executedTools = await messageToLLMTools(
        client,
        model,
        prePrompt,
        prompt,
        TOOLS,
        tool_handlers,
    )

    content = completion.choices[0].message.content or ""

    addToContextWindow(
        prompt,
        content,
        "user input",
        executedTools,
    )

    return prettyResolve(content)


async def model_handler(prompt: str, ctx: PanelContext):
    tool_handlers = {
        **TOOLS_HANDLERS,
        "runInShellCool": partial(TOOLS_HANDLERS["runInShellCool"], write=ctx.write),
    }
    return await agent_worker.run(_process_agent(prompt, tool_handlers))


COMMANDS = [
    Command("/echo", "Repeat the arguments", echo),
    Command("/clear", "Clear the panel", clear_command),
    Command("/exit", "Exit the panel", exit_command),
    Command("/compact", "Compact the context window", compactContext),
]

PANEL_CONFS = {
    "NAME_TEXT": f"{BOLD + BLUE}KML CODE{RESET}",
    "SUBNAME_TEXT": f"{ITALIC}The Tiny Agents Ultimate Framework{RESET}",
    "INPUT_BOX_UPPER_TEXT": f"{DIM}Try typing something{RESET}",
    "THINKING_TEXT": "Thinking...",
    "MODEL_NAME": model,
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
    "MODEL_HANDLER": model_handler,
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

The example runs model requests and tool execution in `AsyncWorker`, keeping the panel responsive. It explicitly saves each exchange with `addToContextWindow`. Shell output is connected to the chat by binding `runInShellCool` to `ctx.write`; the original handler dictionary remains available for console use.

Commands include `/echo`, `/clear`, `/exit`, `/compact`, and `/model` when model options are configured. Run `/model` to open the selector above the input box, move with ↑/↓, choose with Enter, or close it with Esc. You can also select directly with `/model <number or name>`. The selected model is shown in the panel. To use it for future requests, connect `MODEL_SELECT_HANDLER` to the model state read by your handlers:

```python
model_state = {"name": model}

def set_model(model_name: str) -> None:
    model_state["name"] = model_name

# In _process_agent, pass model_state["name"] as the model argument to
# messageToLLMTools. In compactContext, pass it to NewCompactContextWindow.

PANEL_CONFS.update({
    "MODEL_NAME": model_state["name"],
    "MODEL_OPTIONS": ["model-a", "model-b"],
    "MODEL_SELECT_HANDLER": set_model,
})
```

Make compaction handlers read the same `model_state["name"]` if they should use the selected model too. `/compact` runs model-based context compaction through the worker. `/clear` clears the visible chat, not the framework's conversation context. Scroll with PgUp/PgDn, or jump to the beginning and end with Ctrl+Home/Ctrl+End.

## Panel configuration

Pass a dictionary to `initPanel` from `src.Panel.Panel`:

| Key | Purpose |
| --- | --- |
| `NAME_TEXT`, `SUBNAME_TEXT` | Title and subtitle; ANSI formatting is supported. |
| `INPUT_BOX_UPPER_TEXT` | Extra text beside the scrolling hints. |
| `THINKING_TEXT` | Activity label; defaults to `Thinking...`. |
| `MODEL_NAME` | Current model name displayed in the panel; updated after selection. |
| `MODEL_OPTIONS` | Optional list of model IDs that enables the `/model` selector. |
| `MODEL_SELECT_HANDLER` | Optional callback receiving the selected model ID. Use it to update the state read by model and compaction handlers. |
| `MODEL_HANDLER` | Callable receiving `(text, ctx)` and returning a response or `None`; synchronous and async handlers are supported. |
| `COMMANDS` | List of `Command(name, description, handler)` instances. Command handlers receive `(args, ctx)` and may be synchronous or async. |
| `COMMANDS_LIST` | Completion suggestions; defaults to registered command names. |
| `CONTEXT_WINDOW_SIZE` | Function taking no arguments and returning the current usage; defaults to zero. |
| `CONTEXT_WINDOW_MAX` | Positive integer used as the meter's maximum; defaults to `10000`. |
| `THEME` | `default`, `dark`, `light`, or `ocean`; defaults to `default`. |
| `MESSAGE_SPACING` | Number of blank lines between messages; defaults to `1`, and accepts `0`. |
| `STYLE` | Style overrides for the selected theme. |

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

| Tool | Behavior |
| --- | --- |
| `hourNow()` | Returns the current UTC date and time under `utc`. |
| `runInShell(cmd)` | Collects shell output without displaying it. |
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

Use `partial(handler, write=ctx.write)` to connect an output-capable tool to the panel, as shown in the main example.

## Core without the panel

Import the core from `src.tinyAgents` and the panel separately from `src.Panel.Panel`. The request helpers are async functions and must be awaited:

```python
import asyncio
import os

from src.tinyAgents import startClient, messageToLLM, addToContextWindow

async def run():
    client = startClient(os.environ["API_KEY"])
    message = "Hello"
    completion = await messageToLLM(
        client, os.environ["MODEL"], "You are a helpful assistant.", message
    )
    response = completion.choices[0].message.content or ""
    addToContextWindow(message, response, "user input")
    print(response)

asyncio.run(run())
```

This example reads environment variables directly. The helpers retain synchronous SDK calls internally, so applications with an interactive event loop should run them in a worker, as the panel example does.

## Context and API

| API | Purpose |
| --- | --- |
| `startClient(api_key)` | Create the NVIDIA OpenAI-compatible client. |
| `messageToLLM(client, model, prePrompt, message)` | Async request without tool calling; returns the SDK completion. |
| `loadTools(path)` | Load the `tools` array from JSON. |
| `loadToolHandlers(path)` | Import and validate configured Python handlers. |
| `messageToLLMTools(client, model, prePrompt, message, TOOLS, TOOL_HANDLERS)` | Async request with tool execution; returns completion and execution records. |
| `addToContextWindow(message, response, objectType, toolsRunned=[])` | Save an exchange and optional tool records. |
| `contextWindow` | Shared in-memory conversation dictionary. |
| `contextWindowSize()` | Count saved user and response characters. |
| `clearContextWindow()` | Clear the saved conversation. |
| `OldCompactContextWindow(maxSize)` | Remove the oldest exchanges until the size is within a non-negative character limit. |
| `NewCompactContextWindow(client, model)` | Async request for a summary that replaces the saved conversation; must be awaited. |
| `prettyResolve(text)` | Format Markdown headings and emphasis for terminal output. |

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

Version 0.2.2 adds interactive model selection and updates the terminal panel documentation. The framework remains under active development. See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Contributing

Suggestions and contributions are welcome. Open an issue or submit a pull request with a clear description of the change.

## Ownership

Developed under [KML Research Labs](https://github.com/KML-Research-Labs) by [Kauan Mezavila](https://github.com/kauanmezavila).

## License

Released under the [MIT License](LICENSE).
