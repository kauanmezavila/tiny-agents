from __future__ import annotations

import asyncio
import inspect

from Packages.prettyResolver import prettyResolve
from Packages.colors import BOLD, BRIGHT_CYAN, DIM, RESET

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
        serialized_tools=(),
        approval_tools=(),
    ) -> None:
        self.profiles = profiles
        self.selected = list(selected)
        self.model = self.selected[1]
        self.client = startClient(self.profiles, self.selected)
        self.tools = tools
        self.tool_handlers = tool_handlers
        self.serialized_tools = set(serialized_tools)
        self.approval_tools = set(approval_tools)
        self._approval_lock = asyncio.Lock()
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
        on_tool_start,
        on_tool_approval,
    ) -> str:
        completion, executed_tools = await messageToLLMTools(
            request_client,
            request_model,
            self.pre_prompt,
            prompt,
            self.tools,
            tool_handlers,
            serializedTools=self.serialized_tools,
            onToolStart=on_tool_start,
            approvalTools=self.approval_tools,
            onToolApproval=on_tool_approval,
        )
        content = completion.choices[0].message.content or ""
        addToContextWindow(prompt, content, "user input", executed_tools)
        return prettyResolve(content)

    async def model_handler(self, prompt: str, ctx) -> str:
        request_client = self.client
        request_model = self.model
        tool_handlers = dict(self.tool_handlers)
        for name, handler in tool_handlers.items():
            try:
                accepts_writer = "write" in inspect.signature(handler).parameters
            except (TypeError, ValueError):
                accepts_writer = False
            if accepts_writer:
                tool_handlers[name] = (
                    lambda *args, _handler=handler, **kwargs: _handler(
                        *args,
                        write=lambda text: ctx.write(f"{DIM}{text}{RESET}"),
                        **kwargs,
                    )
                )

        async def request_tool_approval(tool_name: str, arguments: dict) -> bool:
            async with self._approval_lock:
                return await ctx.request_approval(tool_name, arguments)

        return await self.worker.run(
            self._process_agent(
                prompt,
                request_client,
                request_model,
                tool_handlers,
                lambda tool_name: ctx.write(
                    f"{BRIGHT_CYAN}⚙ {BOLD}Tool{RESET}"
                    f" {DIM}›{RESET} {BRIGHT_CYAN}{tool_name}{RESET}"
                ),
                request_tool_approval,
            )
        )

    async def compact_context(self, args, ctx) -> None:
        request_client = self.client
        request_model = self.model
        await self.worker.run(NewCompactContextWindow(request_client, request_model))
