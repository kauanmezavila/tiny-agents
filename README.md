<div align="center">
  <table bgcolor="#ffffff">
    <tr><td><img src="imgs/logo.png" alt="Tiny Agents" width="180" /></td></tr>
  </table>
  <h1>Tiny Agents</h1>
  <p>Small building blocks for Python agents and harnesses.</p>
  <p><b>v0.2.5: dumb fixes.</b></p>
</div>

Tiny Agents is a python framework for building harnesses and agents adjusteds exactly for your needs. This version already allows people to create simple harnesses with message sending, context window, tool usage, approval request and creation of commands.

You can build using the functions or with the harness TUI solution, it includes a solution for resolving the async functions.

```python
from tinyAgents import AgentHarness, startClient, messageToLLM
from tinyAgents.core import loadTools
from tinyAgents.harness import AgentHarness
from tinyAgents.panel import initPanel, Command, AsyncWorker
from tinyAgents.colors import BLUE, WHITE
from tinyAgents.formatting import prettyResolve
```

## Providers and models

What models are proved to works on the framework

| Provider     | Models               |
| ------------ | -------------------- |
| NVIDIA NIM   | `openai/gpt-oss-20b` |
| Cloud Ollama | `gpt-oss:20b`        |

## Installation

Install using PyPi:

```bash
python -m pip install by-tiny-agents
```

If you want the panel:

```bash
python -m pip install "by-tiny-agents[panel]"
```

But, if your prefer Git:

```bash
python -m pip install "by-tiny-agents[panel] @ git+https://github.com/kauanmezavila/tiny-agents.git"
```

## Contributing

Suggestions and contributions are always welcome!

## Ownership

Developed under [KML Research Labs](https://github.com/KML-Research-Labs) by [Kauan Mezavila](https://github.com/kauanmezavila).

## License

[MIT License](LICENSE).
