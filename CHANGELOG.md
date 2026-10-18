## [0.2.4]

- Added concurrent execution for tool calls returned in the same model turn. Synchronous handlers run in worker threads; async handlers are awaited.
- Added optional serialization for configured tools and user approval callbacks for tools that need confirmation.
- Added an approval menu to the panel with command previews and approve/deny controls; the example requires approval for shell commands.
- Improved panel tool activity and shell output presentation, including dim output, clearer status colors, and responsive approval-menu layout.
- Moved synchronous OpenAI SDK requests to worker threads so they do not block the async worker loop.
- Preserved separation between core requests, the optional panel, tools, and the application-provided harness callbacks.

## [0.2.3]

- Added `AgentHarness` to the framework to connect provider/model selection, clients, tool execution, conversation context, and panel callbacks.
- Updated the example to keep application configuration and harness construction in `main.py`, while moving reusable agent-to-panel wiring into the framework.
- Added provider-aware model choices. Switching providers recreates the client with that provider's API key and endpoint; custom providers can supply `baseUrl` in their profile.
- Captured the selected client and model together for each request so a selection change cannot mismatch them while a request is starting.

## [0.2.2]

- Added an interactive `/model` selector above the panel input, with arrow-key navigation, Enter to select, and Esc to close; direct selection by model name or number is also available.
- Added `MODEL_OPTIONS` and `MODEL_SELECT_HANDLER` panel configuration, and kept the displayed model name synchronized with selection.
- Restored normal command autocomplete navigation while the model selector is closed and documented selector styles and framework usage.

## [0.2.1]

- Made `NewCompactContextWindow` async and added a `/compact` example that delegates compaction to `AsyncWorker`.
- Fixed command execution to await async handlers and run synchronous handlers in a thread; direct callers must now await `dispatch`.
- Prevented async commands from overlapping model requests or other async commands while keeping `/clear` and `/exit` available.
- Improved panel responsiveness by batching chat updates, caching ANSI formatting, sampling context usage once per render, and animating the spinner only during activity.
- Added six regression tests covering async commands, blocking handlers, overlapping requests, idle rendering, and bursts of tool output.
- Synchronized the README panel example with `main.py`, including `/compact` and its worker integration.

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
