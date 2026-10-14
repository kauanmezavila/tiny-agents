import uuid
from openai import OpenAI
from datetime import datetime, timezone

contextWindow: dict = {}


def startClient(api_key):
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    return client


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


def addToContextWindow(message, response, objectType):
    id = str(uuid.uuid4())
    timeStamp = datetime.now(timezone.utc)

    contextWindow[id] = {
        "timeStamp": timeStamp.isoformat(),
        "type": objectType,
        "objectContent": {
            "userMessage": message,
            "yourResponse": response,
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
