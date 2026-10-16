## [0.2.0]

- Added a terminal panel with scrollable chat, command completion, `/echo`, `/clear`, and `/exit` example commands, and ANSI-formatted messages.
- Added `PanelContext` callbacks for writing messages, clearing the chat, and exiting the panel, including writes from worker threads.
- Added `AsyncWorker` and async request helpers so applications can run model and tool calls outside the panel's UI loop.
- Kept the core independent of panel imports and connected tool output to the UI through application-supplied callbacks.
- Added `runInShell` and `runInShellCool` example tools with captured output and exit codes; `runInShellCool` accepts a `write` callback and defaults to console output.
- Added a reserved activity line with an animated spinner and configurable text above the input hints.
- Added a context progress bar with configurable size callback and maximum, usage-based colors at 70% and 90%, and the model name below it.
- Added `default`, `dark`, `light`, and `ocean` themes, configurable message spacing, and separate styles for user messages, model responses, and errors.
- Standardized framework messages and tool descriptions in English and removed code comments and docstrings.
- Updated the README with the current `main.py` panel example, installation steps, configuration reference, and usage without the panel.

## [0.1.3]

- Added JSON-based tool definitions and dynamic Python handler loading with `loadTools` and `loadToolHandlers`.
- Added `messageToLLMTools` with automatic tool selection, execution records, error results, and a five-round execution limit.
- Added optional tool execution records to `addToContextWindow` through `toolsRunned`.
- Added the `hourNow` example tool, which returns the current UTC date and time, and its configuration files in `Tools/`.
- Updated the README with tool configuration, usage, and current limitations.

## [0.1.2]

- Added new functions to compact the context window by or deleting the older registers or asking the model to summarize
- Added a cleaning context window function
- Updated prettyResolve

## [0.1.1]

- Added an in-memory context window with `addToContextWindow` and `contextWindowSize`.
- Added package metadata and uv support for local installation and locked workflow dependencies.

## [0.1.0]

- Added `startClient` and `messageToLLM` for NVIDIA's OpenAI-compatible API.
- Added `prettyResolve` for formatting Markdown in terminal output.
