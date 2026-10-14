<div align="center">
  <table bgcolor="#ffffff">
    <tr><td><img src="imgs/logo.png" alt="Tiny Agents" width="180" /></td></tr>
  </table>
  <h1>Tiny Agents</h1>
  <p>Small building blocks for Python agents and harnesses.</p>
</div>

Tiny Agents is an early-stage framework for building custom agent harnesses. It currently provides an NVIDIA API client, a simple in-memory conversation context, and terminal formatting utilities.

## Install

Install the framework and its dependencies from a checkout with uv:

```bash
uv sync
```

Or use pip if you do not have uv:

```bash
python -m pip install .
```

Set an NVIDIA API key before making requests:

```bash
export NVIDIA_API_KEY="your-api-key"
```

In PowerShell:

```powershell
$env:NVIDIA_API_KEY = "your-api-key"
```

## Quick start

```python
import os

from src.tinyAgents import (
    addToContextWindow,
    contextWindowSize,
    messageToLLM,
    startClient,
)
from Packages.prettyResolver import prettyResolve

client = startClient(os.environ["NVIDIA_API_KEY"])
prompt = "You are a helpful assistant."
message = "Which number is larger, 9.11 or 9.8?"

completion = messageToLLM(
    client,
    "nvidia/nemotron-3-super-120b-a12b",
    prompt,
    message,
)
response = completion.choices[0].message.content

print(prettyResolve(response))
addToContextWindow(message, response)
print(f"Context size: {contextWindowSize()} characters")
```

Choose a model identifier available to your NVIDIA account. `messageToLLM` returns the full response from the OpenAI SDK.

## API

- `startClient(api_key)` creates an OpenAI SDK client configured for NVIDIA's OpenAI-compatible endpoint.
- `messageToLLM(client, model, prePrompt, message)` sends the system instruction, saved context, and user message; it returns the SDK response.
- `addToContextWindow(message, response)` stores a user message and response in process memory.
- `contextWindowSize()` returns the total character count stored in the context.
- `prettyResolve(text)` formats Markdown headings and bold text for terminal output.

The context is in-memory and is lost when the process exits. Its size is measured in characters, not model tokens.

## Project status

The framework is under active development. The project aims to keep its building blocks small and understandable; tools and agent execution are not implemented yet. See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Contributing

Suggestions and contributions are welcome. Open an issue or submit a pull request with a clear description of the change.

## Ownership

Developed under [KML Research Labs](https://github.com/KML-Research-Labs) by [Kauan Mezavila](https://github.com/kauanmezavila).

## License

Released under the [MIT License](LICENSE).
