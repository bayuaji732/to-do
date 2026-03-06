import os
from openai import OpenAI

# Make sure that you have stored the API Key in the environment variable ARK_API_KEY
# Initialize the Openai client to read your API Key from the environment variable
client = OpenAI(
    # This is the default path. You can configure it based on the service location
    base_url="https://ark.ap-southeast.bytepluses.com/api/v3",
    # Get your API Key from the environment variable
    api_key=os.environ.get("ARK_API_KEY"),
)

# Non-streaming:
print("----- standard request -----")
completion = client.chat.completions.create(
    # Specify the Ark Inference Point ID that you created, which has been changed for you here to your Endpoint ID
    model="deepseek-v3-2-251201",
    messages=[
        {"role": "system", "content": "You're an AI assistant"},
        {"role": "user", "content": "What are the common cruciferous plants?"},
    ],
)
print(completion.choices[0].message.content)

# Streaming:
print("----- streaming request -----")
stream = client.chat.completions.create(
    # Specify the Ark Inference Point ID that you created, which has been changed for you here to your Endpoint ID
    model="deepseek-v3-2-251201",
    messages=[
        {"role": "system", "content": "You're an AI assistant"},
        {"role": "user", "content": "What are the common cruciferous plants?"},
    ],
    # Whether the response content is streamed back
    stream=True,
)
for chunk in stream:
    if not chunk.choices:
        continue
    print(chunk.choices[0].delta.content, end="")
print()