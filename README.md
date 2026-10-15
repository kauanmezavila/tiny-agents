<div align="center">
  <table bgcolor="#ffffff">
    <tr><td><img src="imgs/logo.png" alt="Tiny Agents" width="180" /></td></tr>
  </table>
  <h1>Tiny Agents</h1>
  <p>Small building blocks for Python agents and harnesses.</p>
</div>

Tiny Agents is an early-stage framework for building custom agent harnesses. It currently provides an NVIDIA API client, an in-memory conversation context with clearing and compaction functions, local tool calling configured through JSON files, and terminal formatting utilities.

## Install

Install the framework and its dependencies from a checkout with uv:

```bash
uv sync
```

Or use pip if you do not have uv:

```bash
python -m pip install .
```

The example in `main.py` also uses `python-dotenv`, which is not included in the framework dependencies. Install it with:

```bash
uv pip install python-dotenv
```

Or with pip:

```bash
python -m pip install python-dotenv
```

Create a `.env` file in the project root with your NVIDIA API key and a model identifier available to your account:

```dotenv
API_KEY=your-api-key
MODEL=your-model-id
```

## Quick start

The following example introduces the user, asks the model to recall their name and use a local tool, summarizes the saved context, and asks again. Run it from the project root so the `Tools/` configuration and handler module can be found. Use a model that supports tool calling:

```python
import os
from dotenv import load_dotenv

from src.tinyAgents import *
from Packages.prettyResolver import prettyResolve
from Packages.colors import *

load_dotenv()

apiKey = os.getenv("API_KEY")
model = os.getenv("MODEL")

client = startClient(apiKey)

toolsJsonPath = os.path.join('Tools', 'tools.json')
toolsCallJsonPath = os.path.join('Tools', 'toolsCall.json')

TOOLS = loadTools(toolsJsonPath)
TOOLS_HANDLERS = loadToolHandlers(toolsCallJsonPath)

prePrompt = "You are a helpful agent that gives HUGE and COMPLEX answers"


message = "Hi, my name is Kauan, I'm the founder of KML Group and I'm developing the Tiny Agents framework, by the way, the requests, context window and some other things are running on it"

completion = messageToLLM(client, model, prePrompt, message)


print(DIM, contextWindow, contextWindowSize())
print(completion.choices[0].message.content, RESET)
print("-"*30)
print(prettyResolve(completion.choices[0].message.content))
print("-"*30)

addToContextWindow(message, completion.choices[0].message.content, "user input")
print(DIM, contextWindow, contextWindowSize(), RESET, "\n")


print("="*30)
print("="*30)

message = "What is my name? And what i am making? What time is now, and what is 756 + 534?"

completion, executedTools = messageToLLMTools(client, model, prePrompt, message, TOOLS, TOOLS_HANDLERS)


print(DIM, contextWindow, contextWindowSize())
print(completion.choices[0].message.content, RESET)
print("-"*30)
print(prettyResolve(completion.choices[0].message.content))
print("-"*30)

addToContextWindow(message, completion.choices[0].message.content, "user input", executedTools)
print(DIM, contextWindow, contextWindowSize(), RESET, "\n")


print("="*30)
print("="*30)

NewCompactContextWindow(client, model)

message = "What is my name? And what i am making? What time is now, and what is 756 + 534?"

completion = messageToLLM(client, model, prePrompt, message)


print(DIM, contextWindow, contextWindowSize())
print(completion.choices[0].message.content, RESET)
print("-"*30)
print(prettyResolve(completion.choices[0].message.content))
print("-"*30)

addToContextWindow(message, completion.choices[0].message.content, "user input")
print(DIM, contextWindow, contextWindowSize(), RESET, "\n")
```

Run it from the project root after installing the dependencies and configuring `.env`:

```bash
uv run --with python-dotenv main.py
```

Or with pip and Python:

```bash
python main.py
```

`messageToLLM` returns the full response from the OpenAI SDK. Save each exchange explicitly with `addToContextWindow` so later requests can use it. `NewCompactContextWindow` makes an additional model request and replaces the saved exchanges with a summary; details may be lost during summarization.

## Tool calling

`Tools/tools.json` defines the tools offered to the model using function tool schemas. The included tool, `hourNow`, takes no arguments and returns the current UTC date and time as an ISO 8601 string under the `utc` key. No arithmetic tool is included.

`Tools/toolsCall.json` maps each tool name to a Python handler in `module:function` format:

```json
{
  "hourNow": "Tools.hourNow:hourNow"
}
```

To add a tool, implement an importable Python function, add its name, description, and parameter schema to the `tools` array in a `tools.json` format like, and map the same name to its handler in a `toolsCall.json` format like. Handler keyword arguments must match the schema's parameter names. Load handler mappings from trusted configuration: loading them imports the referenced Python modules.

`messageToLLMTools` lets the model choose tools automatically, runs each requested handler, sends the results back to the model, and returns `(completion, executedTools)`. It allows up to five rounds of tool execution, with multiple calls possible per round. If the model still requests tools after those rounds, it raises `RuntimeError("Tool calls limit exceeded")`.

Each execution record contains `id`, `name`, `arguments`, and `ok`, plus `result` on success or `error` on failure. Unknown tool names, invalid JSON arguments, arguments that are not JSON objects, and handler exceptions are returned to the model as failed tool results. Configuration loading errors and API request errors propagate to the caller.

Tool execution does not automatically save the exchange. Pass `executedTools` to `addToContextWindow` to retain it with the response. For a later call to `messageToLLM`, omit that argument so previous executions are not recorded again.

The `Tools/` examples are part of the repository checkout and are not included in the installed packages. Provide your own configuration paths and importable handlers when using the framework outside the checkout. The examples use `loadTools` from `src.tinyAgents`, which returns the `tools` array; `Packages.tools.loadTools` instead returns the complete JSON document.

## API

- `startClient(api_key)` creates an OpenAI SDK client configured for NVIDIA's OpenAI-compatible endpoint.
- `messageToLLM(client, model, prePrompt, message)` sends the system instruction, saved context, and user message; it returns the SDK response.
- `loadTools(path)` loads the `tools` array from a JSON configuration file.
- `loadToolHandlers(path)` imports the handlers in a JSON name-to-`module:function` mapping and checks that they are callable.
- `messageToLLMTools(client, model, prePrompt, message, TOOLS, TOOL_HANDLERS)` sends a request with tool support and returns the final SDK response and execution records.
- `addToContextWindow(message, response, objectType, toolsRunned=[])` stores an exchange with a UUID, UTC timestamp, type label (for example, `"user input"`), and optional tool execution records under `objectContent.toolsRunned`.
- `contextWindow` is the dictionary containing the saved exchanges.
- `contextWindowSize()` returns the character count of saved user messages and responses, excluding metadata and tool execution records.
- `clearContextWindow()` removes all saved entries.
- `OldCompactContextWindow(maxSize)` removes the oldest entries until the context size is at most `maxSize` characters. Use a non-negative limit.
- `NewCompactContextWindow(client, model)` asks the model to summarize the context and replaces it with a single summary entry.
- `prettyResolve(text)` formats Markdown headings and text enclosed in single or double asterisks for terminal output.

The context is in-memory and is lost when the process exits. Its size is measured in characters, not model tokens.

## Project status

The framework is under active development. The project aims to keep its building blocks small and understandable; local tool calling is available, while broader agent orchestration remains under development. See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Contributing

Suggestions and contributions are welcome. Open an issue or submit a pull request with a clear description of the change.

## Ownership

Developed under [KML Research Labs](https://github.com/KML-Research-Labs) by [Kauan Mezavila](https://github.com/kauanmezavila).

## License

Released under the [MIT License](LICENSE).
