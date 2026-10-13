<div align="center">
  <img src="imgs/logo.png" alt="Tiny Agents" width="180" />
  <h1>Tiny Agents</h1>
  <p>A small starting point for building agents and harnesses with Python.</p>
</div>

---

Tiny Agents is an early-stage project to Terra from [Hack Club](https://hackclub.com/) exploring a simple way to build agents: small functions that make the job 15x times easier.

The goal is to provide small, understandable building blocks for creating custom harnesses.
The focus is on learning and experimentation without hiding how things work behind a large framework.

> The framework isn't complete for now (time expected: 12 weeks)

## What’s ready to use

- A chat client using the `openai` SDK to NVIDIA models with structured response
- A function for sending a system instruction and user message, then receiving the model’s full response.
- Terminal utilities for pretting the responses.

## Getting started

You need Python and an API key compatible with the configured endpoint. Install the SDK:

```bash
python -m pip install openai
```

Set your API key as an environment variable:

```bash
export NVIDIA_API_KEY="your-api-key"
```

On Windows PowerShell:

```powershell
$env:NVIDIA_API_KEY = "your-api-key"
```

Example, run from the repository root:

```python
import os
from dotenv import load_dotenv

from src.tinyAgents import *
from Packages.prettyResolver import prettyResolve

load_dotenv()

apiKey = os.getenv("API_KEY")

client = startClient(apiKey)

prePrompt = "You are a helpful agent that gives HUGE and COMPLEX answers"

completion = messageToLLM(client, "nvidia/nemotron-3-super-120b-a12b", prePrompt, "Which number is larger, 9.11 or 9.8?")

print(completion.choices[0].message.content)
print(prettyResolve(completion.choices[0].message.content))
```

The model identifier depends on which models are available to your NVIDIA account and if have structured responses.

## Frame Functions

This is what is ready to use:

**1. startClient**

```python
startClient(api_key)
```

Starts a OpenAI client.

- api_key: receives the api key

**2. messageToLLM**

```python
messageToLLM(client, model, prePrompt, message)
```

Sends an message to a LLM via API with the client.

- client: usually created using the **startClient** function
- model: the model name, like "nvidia/nemotron-3-super-120b-a12b"
- prePrompt: pre instructions to the model
- message: what you want the model to respond

## Project structure

```text
src/tinyAgents.py          model connection and chat request
Packages/colors.py         terminal display utilities
Packages/prettyResolver.py simple heading and bold-text formatting
```

## Project direction

The project aims to grow through small components that can be combined into a harness: model interaction, context, and eventually tools that let an agent take actions. These features have not been implemented yet.

## Contributing

This project is just getting started. Suggestions, experiments, and contributions are welcome. Open an issue or submit a pull request with a clear description of the change.

## Ownership

The project is being developed under [KML Research Labs](https://github.com/KML-Research-Labs) by [Kauan Mezavila (Most known as BK or ByKurebo)](https://github.com/kauanmezavila)

## License

Released under the [MIT License](LICENSE).
