from openai import OpenAI

def startClient(api_key):
  client = OpenAI(
    base_url = "https://integrate.api.nvidia.com/v1",
    api_key = api_key
  )
  return client

def messageToLLM(client, model, prePrompt, message):
  completion = client.chat.completions.create(
    model=model,
    messages=[{"role":"system","content":prePrompt},{"role":"user","content":message}],
    temperature=0.5,
    top_p=1,
    max_tokens=1024,
    stream=False
  )
  return completion