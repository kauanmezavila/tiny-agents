# Tiny Agents usage

The repository includes a `main.py` runnable example, just make sure to create a .env with a API KEY from NVIDIA NIM and (or) Ollama:

```env
API_KEY_NVIDIA=your-key
API_KEY_OLLAMA=your-key
```

Lets learn how to use with the example:

```python
import os                                                                   # For getting .env values
from dotenv import load_dotenv                                              # For getting .env values
from prompt_toolkit.patch_stdout import patch_stdout                        # To run the panel
                                                                            #
from tinyAgents import *                                                    # Import the main framework
from tinyAgents.panel import initPanel, PanelContext, Command, AsyncWorker  # The panel utils
from tinyAgents.colors import *                                             # The color util

agent_worker = AsyncWorker() # Enable the async in the panel, i MUST be for avoid some weird things

load_dotenv() # Load the .env

apiKeyNvidia = os.getenv("API_KEY_NVIDIA") # Provider API key
apiKeyOllama = os.getenv("API_KEY_OLLAMA") # Provider API key

profiles = { # Here you configures the models + providers
    "nvidia": { # Provider name
        "models": ["openai/gpt-oss-20b"], # Avaliable models
        "apiKey": apiKeyNvidia, # The API key
    },
    "cloud-ollama": {
        "models": ["gpt-oss:20b"],
        "apiKey": apiKeyOllama,
    }
}

selected = ["nvidia", "openai/gpt-oss-20b"] # The default selected model

toolsJsonPath = os.path.join("Tools", "tools.json") # Path resolving for OS-wides
toolsCallJsonPath = os.path.join("Tools", "toolsCall.json") # Same thing here

TOOLS = loadTools(toolsJsonPath) # Load the tools
TOOLS_HANDLERS = loadToolHandlers(toolsCallJsonPath) # Here the handlers

prePrompt = "You are a helpful agent that provides detailed answers. Use tools only when the user asks." # The instructions for the model
agent = AgentHarness( # Here you create a agent for the panel
    profiles=profiles,
    selected=selected,
    tools=TOOLS,
    tool_handlers=TOOLS_HANDLERS,
    pre_prompt=prePrompt,
    worker=agent_worker, # The async
    serialized_tools={"runInShell", "runInShellCool"}, # Tools allowed to run ONLY serialized
    approval_tools={"runInShell", "runInShellCool"}, # Tools that demmands approval
)


def echo(args: list[str], ctx: PanelContext) -> str: # Comand for the panel
    return " ".join(args)


def clear_command(args: list[str], ctx: PanelContext) -> None: # Same here
    ctx.clear()


def exit_command(args: list[str], ctx: PanelContext) -> None: # And here
    ctx.exit()


COMMANDS = [ # The commands slash invocal, the help text, and the function to run
    Command("/echo", "Repeat the arguments", echo),
    Command("/clear", "Clear the panel", clear_command),
    Command("/exit", "Exit the panel", exit_command),
    Command("/compact", "Compact the context window", agent.compact_context),
]

PANEL_CONFS = { # The configs dict, here you configure the entire panel
    "NAME_TEXT": f"{BOLD + BRIGHT_CYAN}JuCode{RESET}",
    "SUBNAME_TEXT": f"{DIM + ITALIC}Powered by Tiny Agents{RESET}",
    "INPUT_BOX_UPPER_TEXT": f"{DIM}Type a message | / for commands | Tab to complete{RESET}",
    "THINKING_TEXT": "Thinking...",
    "MODEL_NAME": agent.model,
    "MODEL_PROVIDER": agent.provider,
    "MODEL_OPTION": agent.model_option,
    "CONTEXT_WINDOW_SIZE": contextWindowSize,
    "CONTEXT_WINDOW_MAX": 10000,
    "THEME": "dark",
    "MESSAGE_SPACING": 1,
    "STYLE": {
        "title": BOLD + BRIGHT_CYAN,
        "user": BG_BLUE + WHITE,
        "model": WHITE,
        "error": RED,
        "separator": DIM + BLACK,
        "hint": DIM,
        "input-field": BG_BLUE + WHITE,
        "completion-menu": BG_BRIGHT_BLACK + WHITE,
        "completion-menu.completion": WHITE,
        "completion-menu.completion.current": BG_BLUE + BOLD + WHITE,
        "radio": DIM + WHITE,
        "radio-checked": BOLD + BRIGHT_CYAN,
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

panel = initPanel(PANEL_CONFS) # init the panel with the confs

with patch_stdout(): # Runs it in loop
    panel.run()

```

## Panel configuration

Everything that you can make with the configuration dict

| Key                         | Purpose                                                                                                      |
| --------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `NAME_TEXT`, `SUBNAME_TEXT` | Title and subtitle for the panel, ANSI is suported                                                           |
| `INPUT_BOX_UPPER_TEXT`      | The text beside the scrolling hints.                                                                         |
| `THINKING_TEXT`             | The activity text for when the model is working; default is `Thinking...`.                                   |
| `MODEL_NAME`                | Current model name displayed in the panel                                                                    |
| `MODEL_PROVIDER`            | Current provider displayed with the model when set.                                                          |
| `MODEL_OPTION`              | Current selector ID, usually `provider::model`                                                               |
| `MODEL_OPTIONS`             | Optional list of model that enables the `/model` selector.                                                   |
| `MODEL_OPTION_LABELS`       | Optional mapping from selector IDs to readable labels                                                        |
| `MODEL_SELECT_HANDLER`      | Optional callback receiving the selected option ID.                                                          |
| `MODEL_HANDLER`             | Callable receiving `(text, ctx)` and returning a response or `None`                                          |
| `COMMANDS`                  | List of `Command(name, description, handler)`. Command handlers receive `(args, ctx)`, can be sync or async. |
| `COMMANDS_LIST`             | Commands completions suggestions; defaults to registered command names.                                      |
| `CONTEXT_WINDOW_SIZE`       | The current window size                                                                                      |
| `CONTEXT_WINDOW_MAX`        | The maximun value, integer; defaults to `10000`.                                                             |
| `THEME`                     | `default`, `dark`, `light`, or `ocean`; the bundled example uses `dark`.                                     |
| `MESSAGE_SPACING`           | Number of blank lines between messages; defaults to `1`, and accepts `0`.                                    |
| `STYLE`                     | Style overrides for the selected theme.                                                                      |

## Tool calling

`Tools/tools.json` defines the function schemas offered to the model. `Tools/toolsCall.json` maps their names to Python handlers:

```json
{
  "hourNow": "Tools.hourNow.hourNow:hourNow",
  "runInShell": "Tools.runInShell.runInShell:runInShell",
  "runInShellCool": "Tools.runInShell.runInShell:runInShellCool",
  "webSearch": "Tools.webSearch.webSearch:webSearch"
}
```

The included tools are examples and conveniences for applications.

### Tools without the panel

Tools do not import the panel. The output callback is supplied by the application and is not a model parameter or part of the JSON schema:

```python
from Tools.runInShell.runInShell import runInShellCool

result = runInShellCool("echo hello")
```

`AgentHarness` connects tools that accept a `write` parameter to the panel's `ctx.write` callback when handling a request.

## Core without the panel

Import the public API from `tinyAgents`. The request helpers are async functions and must be awaited:

```python
import asyncio
import os

from tinyAgents import startClient, messageToLLM, addToContextWindow

async def run():
    model = "openai/gpt-oss-20b"
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

| API                                                                                                                                                       | Purpose                                                                                        |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `startClient(profiles, selected)`                                                                                                                         | Create an OpenAI-compatible client using the selected provider's key and URL.                  |
| `messageToLLM(client, model, prePrompt, message)`                                                                                                         | Async request without tool calling; returns the SDK completion.                                |
| `loadTools(path)`                                                                                                                                         | Load the `tools` array from JSON.                                                              |
| `loadToolHandlers(path)`                                                                                                                                  | Import and validate configured Python handlers.                                                |
| `messageToLLMTools(client, model, prePrompt, message, TOOLS, TOOL_HANDLERS, serializedTools=(), onToolStart=None, approvalTools=(), onToolApproval=None)` | Async request with parallel execution, optional serialized tools, and approval callbacks.      |
| `addToContextWindow(message, response, objectType, toolsRunned=[])`                                                                                       | Save an exchange and optional tool records.                                                    |
| `contextWindow`                                                                                                                                           | Shared in-memory conversation dictionary.                                                      |
| `contextWindowSize()`                                                                                                                                     | Count saved user and response tokens.                                                          |
| `clearContextWindow()`                                                                                                                                    | Clear the saved conversation.                                                                  |
| `OldCompactContextWindow(maxSize)`                                                                                                                        | Remove the oldest exchanges until the size is within a non-negative character limit.           |
| `NewCompactContextWindow(client, model)`                                                                                                                  | Async request for a summary that replaces the saved conversation; must be awaited.             |
| `prettyResolve(text)`                                                                                                                                     | Format Markdown headings, emphasis, lists, fenced code, links, and tables for terminal output. |
| `AgentHarness(...)`                                                                                                                                       | Connect provider/model selection, tool handlers, context, worker, and panel callbacks.         |

Requests do not automatically save their results. Pass `executedTools` to `addToContextWindow` to retain tool records alongside an exchange. Context is shared within the process and is lost when it exits. Model-based compaction makes an additional API request and may lose details.

Compaction follows the same async calling pattern as `messageToLLM`:

```python
await NewCompactContextWindow(client, model)
```

From the panel's UI loop, use the existing worker to keep the synchronous SDK request off the UI thread:

```python
await agent_worker.run(NewCompactContextWindow(client, model))
```
