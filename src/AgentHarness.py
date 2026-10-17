from __future__ import annotations

import inspect

from Packages.prettyResolver import prettyResolve

from .tinyAgents import (
    NewCompactContextWindow,
    addToContextWindow,
    messageToLLMTools,
    startClient,
)


class AgentHarness:

    def __init__(
        self,
        *,
        profiles: dict,
        selected: list[str],
        tools: list[dict],
        tool_handlers: dict,
        pre_prompt: str,
        worker,
    ) -> None:
        self.profiles = profiles
        self.selected = list(selected)
        self.model = self.selected[1]
        self.client = startClient(self.profiles, self.selected)
        self.tools = tools
        self.tool_handlers = tool_handlers
        self.pre_prompt = pre_prompt
        self.worker = worker

    @property
    def provider(self) -> str:
        return self.selected[0]

    @property
    def model_option(self) -> str:
        return f"{self.provider}::{self.model}"

    def model_options(self) -> list[str]:
        return [
            f"{provider}::{model}"
            for provider, profile in self.profiles.items()
            for model in profile.get("models", [])
        ]

    def model_option_labels(self) -> dict[str, str]:
        return {
            f"{provider}::{model}": f"{provider} / {model}"
            for provider, profile in self.profiles.items()
            for model in profile.get("models", [])
        }

    def select_model(self, option: str) -> None:
        provider, model = option.split("::", 1)
        if provider not in self.profiles:
            raise ValueError(f"Unknown provider: {provider}")
        if model not in self.profiles[provider].get("models", []):
            raise ValueError(f"Unknown model for {provider}: {model}")

        # Build the replacement first so failed configuration leaves the
        # current client and selection intact.
        client = self.client
        if provider != self.provider:
            client = startClient(self.profiles, [provider, model])
        self.client = client
        self.selected = [provider, model]
        self.model = model

    async def _process_agent(
        self,
        prompt: str,
        request_client,
        request_model: str,
        tool_handlers: dict,
    ) -> str:
        completion, executed_tools = await messageToLLMTools(
            request_client,
            request_model,
            self.pre_prompt,
            prompt,
            self.tools,
            tool_handlers,
        )
        content = completion.choices[0].message.content or ""
        addToContextWindow(prompt, content, "user input", executed_tools)
        return prettyResolve(content)

    async def model_handler(self, prompt: str, ctx) -> str:
        # Keep the client and model paired if the selection changes while this
        # request is being scheduled on the worker.
        request_client = self.client
        request_model = self.model
        tool_handlers = dict(self.tool_handlers)
        for name, handler in tool_handlers.items():
            try:
                accepts_writer = "write" in inspect.signature(handler).parameters
            except (TypeError, ValueError):
                accepts_writer = False
            if accepts_writer:
                tool_handlers[name] = lambda *args, _handler=handler, **kwargs: _handler(
                    *args, write=ctx.write, **kwargs
                )

        return await self.worker.run(
            self._process_agent(
                prompt, request_client, request_model, tool_handlers
            )
        )

    async def compact_context(self, args, ctx) -> None:
        request_client = self.client
        request_model = self.model
        await self.worker.run(
            NewCompactContextWindow(request_client, request_model)
        )
