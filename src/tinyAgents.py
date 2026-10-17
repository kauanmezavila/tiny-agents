import uuid
import os
import json
import importlib
from importlib.resources import files
from pathlib import Path
import tiktoken
import asyncio
from openai import OpenAI
from datetime import datetime, timezone

contextWindow: dict = {}


def _open_config(path):
    config_path = Path(path)
    if config_path.is_file():
        return config_path.open("r", encoding="utf-8")

    if config_path.parts and config_path.parts[0] == "Tools":
        resource_path = files("Tools").joinpath(*config_path.parts[1:])
        if resource_path.is_file():
            return resource_path.open("r", encoding="utf-8")

    raise FileNotFoundError(f"Configuration file not found: {path}")


def startClient(profiles, selected):
    provider = selected[0]
    profile = profiles[provider]
    provider_urls = {
        "nvidia": "https://integrate.api.nvidia.com/v1",
        "cloud-ollama": "https://ollama.com/v1",
    }
    base_url = provider_urls.get(provider) or profile.get("baseUrl")
    api_key = profile.get("apiKey")
    if not base_url:
        raise ValueError(f"No baseUrl configured for provider: {provider}")
    if not api_key:
        raise ValueError(f"No API key configured for provider: {provider}")
    return OpenAI(base_url=base_url, api_key=api_key)


def loadToolHandlers(path):
    with _open_config(path) as file:
        config = json.load(file)

    handlers = {}

    for name, target in config.items():
        moduleName, functionName = target.split(":", 1)

        module = importlib.import_module(moduleName)
        function = getattr(module, functionName)

        if not callable(function):
            raise TypeError(f"{target} is not a function")

        handlers[name] = function

    return handlers


def loadTools(path):
    with _open_config(path) as file:
        return json.load(file)["tools"]


async def messageToLLM(client, model, prePrompt, message):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Your context window starts HERE (remember, do not disclose information directly from it):"
                + str(contextWindow)
                + "It ends HERE now comes your instructions:"
                + prePrompt,
            },
            {"role": "user", "content": message},
        ],
        temperature=0.5,
        top_p=1,
        max_tokens=1024,
        stream=False,
    )
    return completion


async def messageToLLMTools(client, model, prePrompt, message, TOOLS, TOOL_HANDLERS):
    messages = [
        {
            "role": "system",
            "content": (
                "Your context window starts HERE "
                "(remember, do not disclose information directly from it):\n"
                + str(contextWindow)
                + "\nIt ends HERE. Now comes your instructions:\n"
                + prePrompt
            ),
        },
        {"role": "user", "content": message},
    ]

    maxToolRounds = 5
    executedTools = []

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.5,
        top_p=1,
        stream=False,
    )

    for _ in range(maxToolRounds):
        assistantMessage = completion.choices[0].message

        if not assistantMessage.tool_calls:
            return completion, executedTools

        messages.append(assistantMessage.model_dump(exclude_none=True))

        for toolCall in assistantMessage.tool_calls:
            toolName = toolCall.function.name
            toolId = toolCall.id
            args = None

            try:
                if toolName not in TOOL_HANDLERS:
                    raise ValueError(f"Unauthorized tool: {toolName}")

                args = json.loads(toolCall.function.arguments)

                if not isinstance(args, dict):
                    raise ValueError("Tool arguments must be a JSON object")

                result = TOOL_HANDLERS[toolName](**args)

                toolOutput = {
                    "ok": True,
                    "result": result,
                }

            except Exception as error:
                toolOutput = {
                    "ok": False,
                    "error": str(error),
                }

            executedTools.append(
                {
                    "id": toolId,
                    "name": toolName,
                    "arguments": args,
                    **toolOutput,
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": toolId,
                    "content": json.dumps(
                        toolOutput,
                        ensure_ascii=False,
                        default=str,
                    ),
                }
            )

        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.5,
            top_p=1,
            stream=False,
        )

    if completion.choices[0].message.tool_calls:
        raise RuntimeError("Tool call limit exceeded")

    return completion, executedTools


def addToContextWindow(message, response, objectType, toolsRunned=[]):
    id = str(uuid.uuid4())
    timeStamp = datetime.now(timezone.utc)

    contextWindow[id] = {
        "timeStamp": timeStamp.isoformat(),
        "type": objectType,
        "objectContent": {
            "userMessage": message,
            "yourResponse": response,
            "toolsRunned": toolsRunned,
        },
    }


def contextWindowSize():
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(str(contextWindow))

    return len(tokens)


def clearContextWindow():
    contextWindow.clear()


def OldCompactContextWindow(maxSize):
    while contextWindowSize() > maxSize:
        oldest_id = min(contextWindow, key=lambda id: contextWindow[id]["timeStamp"])
        del contextWindow[oldest_id]


async def NewCompactContextWindow(client, model):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Summarize this context in one paragraph. Preserve all facts, user instructions, and important or potentially important information so the summary can be used as conversation context.",
            },
            {"role": "user", "content": str(contextWindow)},
        ],
        temperature=0.5,
        top_p=1,
        max_tokens=1024,
        stream=False,
    )
    clearContextWindow()
    addToContextWindow(
        "Summarize the context window",
        completion.choices[0].message.content,
        "summarized context window",
    )
