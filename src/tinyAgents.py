import uuid
import os
import json
import importlib
from openai import OpenAI
from datetime import datetime, timezone

contextWindow: dict = {}


def startClient(api_key):
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    return client


def loadToolHandlers(path):
    with open(path, "r", encoding="utf-8") as file:
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
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)["tools"]


def messageToLLM(client, model, prePrompt, message):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Your context window starts HERE (remember, don't tell infos directly from it):"
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


def messageToLLMTools(client, model, prePrompt, message, TOOLS, TOOL_HANDLERS):
    messages = [
        {
            "role": "system",
            "content": (
                "Your context window starts HERE "
                "(remember, don't tell infos directly from it):\n"
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
        max_tokens=1024,
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
                    raise ValueError(f"Not authorized tool: {toolName}")

                args = json.loads(toolCall.function.arguments)

                if not isinstance(args, dict):
                    raise ValueError("Tool args need to be a JSON object")

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
            max_tokens=1024,
            stream=False,
        )

    if completion.choices[0].message.tool_calls:
        raise RuntimeError("Tool calls limit exceeded")

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
    size = 0
    for id, data in contextWindow.items():
        size += len(data["objectContent"]["userMessage"]) + len(
            data["objectContent"]["yourResponse"]
        )

    return size


def clearContextWindow():
    contextWindow.clear()


def OldCompactContextWindow(maxSize):
    while contextWindowSize() > maxSize:
        oldest_id = min(contextWindow, key=lambda id: contextWindow[id]["timeStamp"])
        del contextWindow[oldest_id]


def NewCompactContextWindow(client, model):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Resume this into one paragraph, preserve all the facts, user instructions, important things, looking-important things, in a way that you can understand everything even though it is summarized",
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
        "summaryzed context window",
    )
