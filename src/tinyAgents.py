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
                "content": "Your context window starts HERE:"
                + str(contextWindow)
                + "It ends HEREm now comes your instructions:"
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


def addToContextWindow(message, response):
    id = str(uuid.uuid4())
    timeStamp = datetime.now(timezone.utc)

    contextWindow[id] = {
        "timeStamp": timeStamp.isoformat(),
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
