<div align="center">
  <table bgcolor="#ffffff">
    <tr><td><img src="imgs/logo.png" alt="Tiny Agents" width="180" /></td></tr>
  </table>
  <h1>Tiny Agents</h1>
  <p>Small building blocks for Python agents and harnesses.</p>
</div>

Tiny Agents is an early-stage framework for building custom agent harnesses. It currently provides an NVIDIA API client, an in-memory conversation context with clearing and compaction functions, and terminal formatting utilities.

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

The following example uses all the functions. It introduces the user, asks the model to recall their name using the saved context, summarizes that context, and asks again:

```python
import os
from dotenv import load_dotenv

from src.tinyAgents import *
from Packages.prettyResolver import prettyResolve

load_dotenv()

apiKey = os.getenv("API_KEY")
model = os.getenv("MODEL")

client = startClient(apiKey)

prePrompt = "You are a helpful agent that gives HUGE and COMPLEX answers"


message = "Hi, my name is Kauan, I'm the founder of KML Group and I'm developing the Tiny Agents framework, by the way, the requests, context window and some other things are running on it"

completion = messageToLLM(client, model, prePrompt, message)


print(contextWindow, contextWindowSize())
print(completion.choices[0].message.content)
print(prettyResolve(completion.choices[0].message.content))

addToContextWindow(message, completion.choices[0].message.content, "user input")
print(contextWindow, contextWindowSize())


print("="*30)
print("="*30)

message = "What is my name? And what i am making?"

completion = messageToLLM(client, model, prePrompt, message)


print(contextWindow, contextWindowSize())
print(completion.choices[0].message.content)
print(prettyResolve(completion.choices[0].message.content))

addToContextWindow(message, completion.choices[0].message.content, "user input")
print(contextWindow, contextWindowSize())


print("="*30)
print("="*30)

NewCompactContextWindow(client, model)

message = "What is my name? And what i am making and what i founded?"

completion = messageToLLM(client, model, prePrompt, message)


print(contextWindow, contextWindowSize())
print(completion.choices[0].message.content)
print(prettyResolve(completion.choices[0].message.content))

addToContextWindow(message, completion.choices[0].message.content, "user input")
print(contextWindow, contextWindowSize())
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

## API

- `startClient(api_key)` creates an OpenAI SDK client configured for NVIDIA's OpenAI-compatible endpoint.
- `messageToLLM(client, model, prePrompt, message)` sends the system instruction, saved context, and user message; it returns the SDK response.
- `addToContextWindow(message, response, objectType)` stores an exchange with a UUID, UTC timestamp, and type label (for example, `"user input"`).
- `contextWindow` is the dictionary containing the saved exchanges.
- `contextWindowSize()` returns the character count of saved user messages and responses, excluding metadata.
- `clearContextWindow()` removes all saved entries.
- `OldCompactContextWindow(maxSize)` removes the oldest entries until the context size is at most `maxSize` characters. Use a non-negative limit.
- `NewCompactContextWindow(client, model)` asks the model to summarize the context and replaces it with a single summary entry.
- `prettyResolve(text)` formats Markdown headings and text enclosed in single or double asterisks for terminal output.

The context is in-memory and is lost when the process exits. Its size is measured in characters, not model tokens.

## Project status

The framework is under active development. The project aims to keep its building blocks small and understandable; tools and agent execution are not implemented yet. See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Contributing

Suggestions and contributions are welcome. Open an issue or submit a pull request with a clear description of the change.

## Ownership

Developed under [KML Research Labs](https://github.com/KML-Research-Labs) by [Kauan Mezavila](https://github.com/kauanmezavila).

## License

Released under the [MIT License](LICENSE).
