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
